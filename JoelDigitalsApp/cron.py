"""Cron-Endpunkte fuer die Joel Digitals App.

Gedacht fuer einen externen Scheduler (z.B. FastCron), der diese URL
regelmaessig aufruft. Wird fuer Ereignisse gebraucht, die zeitbasiert sind
und sich daher NICHT per Django-Signal ausloesen lassen - z.B. ein Artikel,
dessen geplante Veroeffentlichungszeit (published_at) gerade erreicht wurde.

Bestellstatus-Aenderungen (z.B. neuer Sendungsstatus) werden bereits in
Echtzeit per Signal gepusht, siehe JoelDigitalsApp/signals.py - die brauchen
diesen Cron nicht.

Verschickt bei jedem Aufruf auch faellige JoelDigitalsApp.models.PendingPush-
Eintraege (siehe _send_pending_pushes) - die generische Warteschlange fuer
Pushes, die NICHT sofort im ausloesenden Request verschickt werden sollen
(z.B. neue Terminanfragen), gesammelt und dedupliziert (sent_at wird atomar
gesetzt) statt synchron/duplikatanfaellig.
"""
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .services.push import send_push_notification, check_onesignal_credentials

ONESIGNAL_CHECK_INTERVAL_DAYS = 10


def _send_pending_pushes(now, limit=100):
    """Verschickt faellige PendingPush-Eintraege. sent_at wird per .update()
    ATOMAR gesetzt, BEVOR tatsaechlich gesendet wird, damit ein Eintrag auch
    bei ueberlappenden Cron-Aufrufen nie doppelt verschickt wird."""
    from .models import PendingPush

    pending_ids = list(
        PendingPush.objects.filter(sent_at__isnull=True)
        .order_by('created_at')
        .values_list('id', flat=True)[:limit]
    )
    if not pending_ids:
        return []

    PendingPush.objects.filter(id__in=pending_ids, sent_at__isnull=True).update(sent_at=now)

    sent = []
    for push in PendingPush.objects.filter(id__in=pending_ids):
        send_push_notification(
            title=push.title,
            message=push.message,
            user_ids=push.user_ids,
            url=push.url or None,
            data=push.data,
        )
        sent.append(push.id)
    return sent


def _maybe_check_onesignal_health(now):
    """Prueft die OneSignal-Zugangsdaten hoechstens alle 10 Tage (nicht bei
    jedem Cron-Aufruf), und schickt bei einem Fehlschlag eine Warnmail an den
    Support, damit ein rotierter/ungueltiger Key nicht unbemerkt bleibt."""
    from .models import PushHealthCheck

    last_check = PushHealthCheck.objects.first()
    if last_check and (now - last_check.checked_at) < timedelta(days=ONESIGNAL_CHECK_INTERVAL_DAYS):
        return None

    success, detail = check_onesignal_credentials()
    check = PushHealthCheck.objects.create(success=success, detail=detail)

    if not success:
        try:
            from django.core.mail import send_mail
            send_mail(
                subject="⚠️ OneSignal Push-Check fehlgeschlagen",
                message=(
                    f"Der 10-taegige OneSignal-Zugangsdaten-Check ist fehlgeschlagen:\n\n{detail}\n\n"
                    "Push-Benachrichtigungen funktionieren aktuell vermutlich nicht. "
                    "Bitte ONESIGNAL_APP_ID / ONESIGNAL_REST_API_KEY pruefen."
                ),
                from_email=settings.COMPANY_EMAIL_NO_REPLY,
                recipient_list=[settings.SUPPORT_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass

    return {'success': success, 'detail': detail, 'checked_at': check.checked_at.isoformat()}


@csrf_exempt
def push_check(request):
    secret = getattr(settings, 'CRON_SECRET', None)
    if secret and request.GET.get('token', '') != secret:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    from blog.models import BlogPost

    now = timezone.now()
    # Fenster von 7 Tagen: verhindert, dass wirklich alte/migrierte Artikel
    # gepusht werden, ist aber grosszuegig genug, dass ein laengerer Cron-
    # Ausfall (z.B. falsch konfigurierter externer Trigger) einen frisch
    # veroeffentlichten Artikel nicht dauerhaft aus dem Fenster faellt und nie
    # gepusht wird - genau das ist am 2026-07-19 passiert (24h-Fenster war zu
    # knapp, der Cron lief zwischenzeitlich wegen eines Token-Problems nicht).
    window_start = now - timedelta(days=7)

    notified_articles = []
    new_posts = BlogPost.objects.filter(
        is_published=True,
        push_notified_at__isnull=True,
        published_at__lte=now,
        published_at__gte=window_start,
    )
    for post in new_posts:
        send_push_notification(
            title="Neuer Artikel",
            message=post.title_de,
            url=f"https://www.joel-digitals.de/de/blog/{post.slug}/",
        )
        post.push_notified_at = now
        post.save(update_fields=['push_notified_at'])
        notified_articles.append(post.slug)

    pending_pushes_sent = _send_pending_pushes(now)
    onesignal_health = _maybe_check_onesignal_health(now)

    # Kunden nachtraeglich an JDS Management melden, die noch keine Kundennummer
    # haben oder deren letzter Sync-Versuch fehlgeschlagen ist (API-Ausfall,
    # oder ein Kunde, der schon vor Einfuehrung dieses Features existierte) -
    # siehe shop_ourapps.services.jds_api.sync_pending_customers.
    jds_customers_synced = []
    try:
        from shop_ourapps.services.jds_api import sync_pending_customers
        jds_customers_synced = sync_pending_customers()
    except Exception:
        pass

    return JsonResponse({
        'checked_at': now.isoformat(),
        'articles_notified': notified_articles,
        'pending_pushes_sent': pending_pushes_sent,
        'jds_customers_synced': jds_customers_synced,
        'onesignal_health_check': onesignal_health,
    })
