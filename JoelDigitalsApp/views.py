from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from blog.models import BlogPost
from contact.views import is_Sales_Editor, is_Support_Editor, is_Support_Ticket_Admin
from shop_ourapps.models import App as ShopApp, Wallet
from shop_ourapps.models import Order
from status.models import App as StatusApp
from status.models import GlobalIssue
from status.utils import build_hotline_texts, apply_issue_language


def _nav_context(user):
    groups = list(user.groups.values_list('name', flat=True)) if user.is_authenticated else []
    ctx = {
        'user_groups': groups,
        'in_support_sales': 'Selling' in groups,
        'in_support_tickets': 'Support' in groups,
        'in_support_admin': 'Admin Support' in groups,
        'jd_is_admin': user.is_authenticated and (
            user.is_superuser or is_Support_Ticket_Admin(user) or is_Support_Editor(user) or is_Sales_Editor(user)
        ),
        'ONESIGNAL_APP_ID': settings.ONESIGNAL_APP_ID,
    }
    return ctx


def jd_login_app(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    next_is_safe = next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url if next_is_safe else 'jd_home_app')
    else:
        form = AuthenticationForm()
    return render(request, 'jd/login.html', {'form': form, 'next': next_url if next_is_safe else ''})


@login_required(login_url='jd_login_app')
@require_POST
def jd_save_onesignal_player_id_app(request):
    """Speichert die OneSignal-Player-ID der Joel Digitals App. Wird von
    base_app.html bei JEDEM Seitenaufruf einer eingeloggten Session ueber die
    median.co JavaScript-Bridge (median.onesignal.onesignalInfo()) aufgerufen -
    nicht nur einmalig beim Login. Gleiches Muster wie
    save_onesignal_player_id_app() im JDS-Chat-Projekt bzw.
    save_onesignal_player_id() im JDS-Management-Projekt: dort war die ID an
    das Login-Formular gekoppelt, wo der Nutzer noch nicht eingeloggt ist und
    die ID daher praktisch nie ankam."""
    from main.models import UserProfile
    from .services.push import send_push_notification

    player_id = request.POST.get('player_id', '').strip()
    debug = request.POST.get('debug', '').strip()

    if player_id:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        previous_player_id = profile.onesignal_player_id
        if player_id != previous_player_id:
            # War schon eine ANDERE Player-ID gespeichert (nicht nur die
            # allererste Registrierung) -> sieht nach einer Anmeldung auf
            # einem neuen/anderen Geraet aus. Push geht bewusst an die ALTE
            # ID, damit das bisherige Geraet ueber die neue Anmeldung
            # informiert wird (kein eigenes Geraete-Verzeichnis vorhanden,
            # daher nur eine Naeherung statt einer echten Geraeteliste).
            if previous_player_id:
                send_push_notification(
                    title="Neue Anmeldung erkannt",
                    message="Dein Konto wurde soeben auf einem anderen Gerät verwendet. Warst du das nicht, ändere bitte dein Passwort.",
                    user_ids=[request.user.id],
                )
            profile.onesignal_player_id = player_id
            profile.last_onesignal_sync = timezone.now()
            profile.save(update_fields=['onesignal_player_id', 'last_onesignal_sync'])
    elif debug:
        import logging
        logging.getLogger(__name__).warning(
            "OneSignal-Erfassung (Joel Digitals App) ohne gueltige ID fuer User %s: %s",
            request.user.username, debug,
        )
    return JsonResponse({'status': 'ok'})


def jd_logout_app(request):
    logout(request)
    return redirect('jd_login_app')


def jd_register_app(request):
    from main.views import register_view
    request.base_template = 'base_app.html'
    return register_view(request)


@login_required(login_url='jd_login_app')
def jd_home_app(request):
    from shop_ourapps.models import AffiliatePartner, Wallet

    context = _nav_context(request.user)

    deals_preview = [app for app in ShopApp.objects.filter(is_active=True, discount_percent__gt=0) if app.discount_is_active][:4]
    articles_preview = BlogPost.objects.filter(
        is_published=True, published_at__lte=timezone.now()
    ).order_by('-published_at')[:3]

    wallet = Wallet.objects.filter(user=request.user).first()

    context.update({
        'deals_preview': deals_preview,
        'articles_preview': articles_preview,
        'orders_preview': Order.objects.filter(user=request.user).order_by('-created_at')[:3],
        'wallet_balance': wallet.balance if wallet else None,
        'is_affiliate': AffiliatePartner.objects.filter(user=request.user, approved=True).exists(),
    })

    return render(request, 'jd/home.html', context)


@login_required(login_url='jd_login_app')
def jd_deals_app(request):
    context = _nav_context(request.user)
    candidates = ShopApp.objects.filter(is_active=True, discount_percent__gt=0).order_by('-discount_start')
    deals = [app for app in candidates if app.discount_is_active]

    for app in deals:
        app.external_url = request.build_absolute_uri(reverse('app_detail', args=[app.slug]))

    context['deals'] = deals
    return render(request, 'jd/deals.html', context)


@login_required(login_url='jd_login_app')
def jd_articles_app(request):
    context = _nav_context(request.user)
    posts = list(BlogPost.objects.filter(
        is_published=True, published_at__lte=timezone.now()
    ).order_by('-published_at')[:30])

    for post in posts:
        post.external_url = request.build_absolute_uri(reverse('blog_detail', args=[post.slug]))

    context['articles'] = posts
    return render(request, 'jd/articles.html', context)


@login_required(login_url='jd_login_app')
def jd_orders_app(request):
    context = _nav_context(request.user)
    context['orders'] = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'jd/orders.html', context)


@login_required(login_url='jd_login_app')
def jd_order_detail_app(request, order_id):
    from shop_ourapps.models import ReturnRequest

    context = _nav_context(request.user)
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related('app', 'package')
    context['order'] = order
    context['items'] = items
    context['shipment'] = getattr(order, 'shipment', None)
    context['status_logs'] = order.status_logs.all()
    context['can_request_callback'] = _callback_available(order)

    has_returnable_item = any(
        (item.app and (item.app.refundable or item.app.exchangeable))
        or (item.package and False)
        for item in items
    )
    has_open_return = ReturnRequest.objects.filter(order=order, user=request.user).exclude(status='rejected').exists()
    context['can_request_return'] = (
        has_returnable_item
        and not has_open_return
        and order.status in ('Paid', 'In Delivery', 'Delivered', 'Finished')
    )
    return render(request, 'jd/order_detail.html', context)


CALLBACK_WINDOW_DAYS = 14


def _callback_available(order):
    """Rückruf ist waehrend der Bearbeitung jederzeit moeglich, nach Abschluss
    (Zustellung bzw. Endstatus) aber nur noch fuer CALLBACK_WINDOW_DAYS Tage."""
    completed_at = order.delivered_at
    if not completed_at and order.status in ('Finished', 'Canceled', 'Return'):
        completed_at = order.created_at
    if not completed_at:
        return True
    return timezone.now() - completed_at <= timedelta(days=CALLBACK_WINDOW_DAYS)


@login_required(login_url='jd_login_app')
def jd_request_callback_app(request, order_id):
    """Legt einen Rueckrufwunsch an - bewusst KEIN Support-Ticket, sondern ein
    eigener, schlanker CallbackRequest-Eintrag + Benachrichtigungsmail an den
    Support, damit Rueckrufwuensche nicht die normale Ticket-Warteschlange
    aufblaehen."""
    from django.contrib import messages
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import CallbackRequest

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method != 'POST':
        return redirect('jd_order_detail_app', order_id=order.id)

    if not _callback_available(order):
        messages.error(request, f'Ein Rückruf ist nur bis {CALLBACK_WINDOW_DAYS} Tage nach Abschluss der Bestellung möglich.')
        return redirect('jd_order_detail_app', order_id=order.id)

    phone = request.POST.get('phone', '').strip()
    CallbackRequest.objects.create(user=request.user, order=order, phone=phone)

    try:
        send_mail(
            subject=f"Rückrufwunsch - Bestellung #{order.id}",
            message=(
                f"{request.user.get_full_name() or request.user.username} bittet um Rückruf zu Bestellung #{order.id}.\n"
                f"Rückrufnummer: {phone or order.phone}\n"
                f"E-Mail: {request.user.email}"
            ),
            from_email=settings.COMPANY_EMAIL_NO_REPLY,
            recipient_list=[settings.SUPPORT_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass

    messages.success(request, 'Dein Rückrufwunsch wurde übermittelt - wir melden uns bei dir.')
    return redirect('jd_order_detail_app', order_id=order.id)


@login_required(login_url='jd_login_app')
def jd_request_return_app(request, order_id):
    from shop_ourapps.views import request_return
    request.base_template = 'base_app.html'
    return request_return(request, order_id)


@login_required(login_url='jd_login_app')
def jd_admin_dashboard_app(request):
    """Zeigt exakt dasselbe Admin-Dashboard wie main.views.admin_dashboard,
    nur im App-Design (base_app.html statt base_home.html)."""
    from main.views import _build_admin_dashboard_context, _handle_admin_dashboard_actions

    nav = _nav_context(request.user)
    if not nav['jd_is_admin']:
        return redirect('jd_home_app')

    action_response = _handle_admin_dashboard_actions(request, 'jd_admin_dashboard_app')
    if action_response is not None:
        return action_response

    context = _build_admin_dashboard_context(request)
    context.update(nav)
    context['base_template'] = 'base_app.html'
    context['dashboard_url_name'] = 'jd_admin_dashboard_app'
    return render(request, 'main/admin_dashboard.html', context)


@login_required(login_url='jd_login_app')
def jd_status_app(request):
    context = _nav_context(request.user)
    lang = request.LANGUAGE_CODE

    apps = StatusApp.objects.filter(is_active=True).prefetch_related('issues')
    global_issues = list(GlobalIssue.objects.filter(is_resolved=False))
    for issue in global_issues:
        apply_issue_language(issue, lang)

    status_data = []
    issue_apps = []
    for app in apps:
        latest = app.statuses.order_by('-timestamp').first()
        unresolved = [apply_issue_language(i, lang) for i in app.issues.all() if not i.is_resolved]
        entry = {'app': app, 'latest': latest, 'issues': unresolved}
        status_data.append(entry)
        if unresolved:
            issue_apps.append(entry)

    online = sum(1 for s in status_data if s['latest'] and s['latest'].status == 'online')
    offline = sum(1 for s in status_data if s['latest'] and s['latest'].status == 'offline')
    issues = sum(1 for s in status_data if s['issues'])
    total = len(status_data)

    hotline_de, hotline_en = build_hotline_texts(
        list(global_issues), issue_apps, total, online, offline, issues
    )

    context.update({
        'status_data': status_data,
        'global_issues': global_issues,
        'online': online,
        'offline': offline,
        'issues': issues,
        'total': total,
        'hotline_text_de': hotline_de,
        'hotline_text_en': hotline_en,
    })
    return render(request, 'jd/status.html', context)


@login_required(login_url='jd_login_app')
def jd_support_app(request):
    """Native Support-Ticket-Liste in der App - ruft MobileApp.support_tickets_app
    direkt auf (gleiche Logik/Templates wie die Support-App), nur im App-Design."""
    from MobileApp.views import support_tickets_app
    request.base_template = 'base_app.html'
    return support_tickets_app(request)


@login_required(login_url='jd_login_app')
def jd_ticket_detail_app(request, ticket_number):
    from MobileApp.views import ticket_detail_app
    request.base_template = 'base_app.html'
    return ticket_detail_app(request, ticket_number)


# ========================================================================
# Admin-Unterseiten im App-Design
#
# Diese Views rufen die bestehenden Desktop-Views unveraendert auf (inkl.
# deren eigener Berechtigungspruefung) und setzen davor nur
# request.base_template = 'base_app.html'. Die jeweiligen Templates lesen
# das ueber {% extends request.base_template|default:"base_home.html" %},
# wodurch exakt dieselbe Logik/Daten im App-Design statt im Desktop-Design
# gerendert werden - ohne Code-Duplizierung.
# ========================================================================

@login_required(login_url='jd_login_app')
def jd_blog_admin_app(request):
    from blog.views import admin_blog
    request.base_template = 'base_app.html'
    return admin_blog(request)


@login_required(login_url='jd_login_app')
def jd_blog_create_app(request):
    from blog.views import blog_create
    request.base_template = 'base_app.html'
    return blog_create(request)


@login_required(login_url='jd_login_app')
def jd_newsletter_app(request):
    from main.views import newsletter_list
    request.base_template = 'base_app.html'
    return newsletter_list(request)


@login_required(login_url='jd_login_app')
def jd_order_admin_app(request):
    from shop_ourapps.views import order_admin
    request.base_template = 'base_app.html'
    return order_admin(request)


@login_required(login_url='jd_login_app')
def jd_new_order_app(request):
    from shop_ourapps.views import admin_create_order
    request.base_template = 'base_app.html'
    return admin_create_order(request)


@login_required(login_url='jd_login_app')
def jd_tools_app(request):
    from status.views import tools_overview
    request.base_template = 'base_app.html'
    return tools_overview(request)


@login_required(login_url='jd_login_app')
def jd_wallet_app(request):
    from shop_ourapps.views import wallet_view
    request.base_template = 'base_app.html'
    return wallet_view(request)


@login_required(login_url='jd_login_app')
def jd_affiliate_dashboard_app(request):
    from shop_ourapps.views import affiliate_dashboard
    request.base_template = 'base_app.html'
    return affiliate_dashboard(request)


@login_required(login_url='jd_login_app')
def jd_profile_app(request):
    from main.views import profile_view
    request.base_template = 'base_app.html'
    return profile_view(request)


@login_required(login_url='jd_login_app')
def jd_profile_edit_app(request):
    from main.views import profile_edit
    request.base_template = 'base_app.html'
    return profile_edit(request)


@login_required(login_url='jd_login_app')
def jd_change_password_app(request):
    from main.views import change_password
    request.base_template = 'base_app.html'
    return change_password(request)


@login_required(login_url='jd_login_app')
def jd_settings_app(request):
    from status.models import App as StatusApp
    from .models import StatusSubscription
    from main.models import UserProfile

    context = _nav_context(request.user)
    context['status_apps'] = StatusApp.objects.filter(is_active=True).order_by('name')
    context['subscribed_app_ids'] = set(
        StatusSubscription.objects.filter(user=request.user).values_list('app_id', flat=True)
    )
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    context['push_enabled'] = profile.push_enabled
    return render(request, 'jd/settings.html', context)


@login_required(login_url='jd_login_app')
@require_POST
def jd_toggle_status_subscription_app(request, app_id):
    """Schaltet ein Stoerungs-Push-Abo fuer eine status.App an/aus - steuert,
    fuer welche Apps der Nutzer bei neuen AppIssues benachrichtigt wird."""
    from status.models import App as StatusApp
    from .models import StatusSubscription

    app = get_object_or_404(StatusApp, id=app_id, is_active=True)
    sub, created = StatusSubscription.objects.get_or_create(user=request.user, app=app)
    if not created:
        sub.delete()
        return JsonResponse({'subscribed': False})
    return JsonResponse({'subscribed': True})


@login_required(login_url='jd_login_app')
@require_POST
def jd_toggle_push_notifications_app(request):
    """Speichert ob der Nutzer Push-Benachrichtigungen wuenscht."""
    from main.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.push_enabled = request.POST.get('enabled', 'true') == 'true'
    profile.save(update_fields=['push_enabled'])
    return JsonResponse({'push_enabled': profile.push_enabled})


@login_required(login_url='jd_login_app')
def jd_app_permissions_app(request):
    from main.views import app_permissions
    request.base_template = 'base_app.html'
    return app_permissions(request)


@login_required(login_url='jd_login_app')
def jd_delete_account_app(request):
    from main.views import delete_account
    request.base_template = 'base_app.html'
    return delete_account(request)


