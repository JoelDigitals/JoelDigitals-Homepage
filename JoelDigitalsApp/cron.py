"""Cron-Endpunkte fuer die Joel Digitals App.

Gedacht fuer einen externen Scheduler (z.B. FastCron), der diese URL
regelmaessig aufruft. Wird fuer Ereignisse gebraucht, die zeitbasiert sind
und sich daher NICHT per Django-Signal ausloesen lassen - z.B. ein Artikel,
dessen geplante Veroeffentlichungszeit (published_at) gerade erreicht wurde.

Bestellstatus-Aenderungen (z.B. neuer Sendungsstatus) werden bereits in
Echtzeit per Signal gepusht, siehe JoelDigitalsApp/signals.py - die brauchen
diesen Cron nicht.
"""
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .services.push import send_push_notification


@csrf_exempt
def push_check(request):
    secret = getattr(settings, 'CRON_SECRET', None)
    if secret and request.GET.get('token', '') != secret:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    from blog.models import BlogPost

    now = timezone.now()
    # Fenster von 24h: verhindert, dass ein einmalig verpasster Cron-Lauf
    # (Ausfall, Deploy, etc.) einen alten Artikel Tage spaeter noch pusht.
    window_start = now - timedelta(hours=24)

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

    return JsonResponse({
        'checked_at': now.isoformat(),
        'articles_notified': notified_articles,
    })
