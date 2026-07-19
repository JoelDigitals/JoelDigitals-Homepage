# jds_configurator/views.py
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from shop_ourapps.models import App, Cart, CartItem
from .models import (
    JdsModule, JdsConfigRequest, JdsConfiguration, JdsFeatureRequest, calculate_totals,
    extra_users_total, EXTRA_USER_FIRST_PRICE, EXTRA_USER_PRICE_STEP, EXTRA_USER_MIN_PRICE,
)

JDS_APP_SLUG = 'jds-management-individuell'


def _customer_fields(request):
    return {
        'first_name': request.POST.get('first_name', '').strip(),
        'last_name': request.POST.get('last_name', '').strip(),
        'email': request.POST.get('email', '').strip(),
        'phone': request.POST.get('phone', '').strip(),
        'company_name': request.POST.get('company_name', '').strip(),
        'address': request.POST.get('address', '').strip(),
        'zip_code': request.POST.get('zip_code', '').strip(),
        'city': request.POST.get('city', '').strip(),
        'vat_number': request.POST.get('vat_number', '').strip(),
        'notes': request.POST.get('notes', '').strip(),
    }


def _selected_modules(request):
    keys = request.POST.getlist('modules')
    return JdsModule.objects.filter(key__in=keys, is_core=False, is_active=True)


def _extra_users(request):
    try:
        return max(0, int(request.POST.get('extra_users', 0)))
    except ValueError:
        return 0


def configurator_context():
    """Kontext für den Konfigurator (Modulauswahl + Preise) - wird sowohl von
    wizard() als auch von shop_ourapps.views.app_detail() genutzt, damit die
    Produktseite denselben Konfigurator einbetten kann statt nur zu verlinken."""
    core_modules = JdsModule.objects.filter(is_core=True, is_active=True)
    addon_modules = JdsModule.objects.filter(is_core=False, is_active=True)
    categories = {}
    for m in addon_modules:
        categories.setdefault(m.category, []).append(m)
    category_labels = dict(JdsModule.CATEGORY_CHOICES)

    return {
        'core_modules': core_modules,
        'categories': [
            {'key': key, 'label': category_labels.get(key, key), 'modules': mods}
            for key, mods in categories.items()
        ],
        'basismodul_price': JdsConfigRequest.BASISMODUL_PRICE,
        'included_users': JdsConfigRequest.INCLUDED_USERS,
        'extra_user_first_price': EXTRA_USER_FIRST_PRICE,
        'extra_user_price_step': EXTRA_USER_PRICE_STEP,
        'extra_user_min_price': EXTRA_USER_MIN_PRICE,
    }


def wizard(request):
    return render(request, 'jds_configurator/wizard.html', configurator_context())


def _build_offer_context(request):
    customer = _customer_fields(request)
    addon_modules = list(_selected_modules(request))
    extra_users = _extra_users(request)

    total = calculate_totals(JdsConfigRequest.BASISMODUL_PRICE, addon_modules, extra_users)

    return {
        'customer': customer,
        'addon_modules': addon_modules,
        'extra_users': extra_users,
        'extra_users_total': extra_users_total(extra_users),
        'included_users': JdsConfigRequest.INCLUDED_USERS,
        'basismodul_price': JdsConfigRequest.BASISMODUL_PRICE,
        'total': total,
    }


def download_offer_pdf(request):
    if request.method != 'POST':
        return redirect('jds_configurator:wizard')
    context = _build_offer_context(request)
    context['now'] = timezone.now()

    html_string = render_to_string('jds_configurator/offer_pdf.html', context)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_file, encoding='UTF-8')
    if pisa_status.err:
        return HttpResponse('Fehler beim Erstellen des Angebots-PDFs.', status=500)

    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Angebot_JDS_Management.pdf"'
    return response


def submit_request(request):
    if request.method != 'POST':
        return redirect('jds_configurator:wizard')

    customer = _customer_fields(request)
    if not customer['first_name'] or not customer['last_name'] or not customer['email']:
        messages.error(request, "Bitte Name und E-Mail-Adresse angeben.")
        return redirect('jds_configurator:wizard')

    addon_modules = _selected_modules(request)
    extra_users = _extra_users(request)

    config_request = JdsConfigRequest.objects.create(**customer, extra_users=extra_users)
    config_request.modules.set(addon_modules)
    config_request.recalculate_totals()
    config_request.save()

    return render(request, 'jds_configurator/thanks.html', {'config_request': config_request})


@login_required
@require_POST
def add_to_cart(request):
    """Legt die aktuelle Konfigurator-Auswahl (Zusatzmodule + Zusatz-User) als
    JdsConfiguration-Preis-Snapshot an und packt sie als CartItem in den normalen
    Shop-Warenkorb - von dort läuft alles über den regulären Checkout (Login,
    Zahlungsart, Rechnung), genau wie bei jedem anderen Produkt."""
    addon_modules = _selected_modules(request)
    extra_users = _extra_users(request)

    configuration = JdsConfiguration.objects.create(extra_users=extra_users)
    configuration.modules.set(addon_modules)
    configuration.recalculate_totals()
    configuration.save()

    jds_app = get_object_or_404(App, slug=JDS_APP_SLUG)
    cart, _created = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.create(
        user=request.user,
        cart=cart,
        app=jds_app,
        jds_configuration=configuration,
        quantity=1,
        price=configuration.total_amount,
    )

    messages.success(request, "Dein individuelles JDS Management wurde in den Warenkorb gelegt.")
    return redirect('cart_view')


def _notify_staff_of_feature_request(feature_request, request):
    """Benachrichtigt das Team per Mail + Push über einen neuen Funktionswunsch,
    damit die Anfrage im Admin-Dashboard (Desktop & /app/) zeitnah gesichtet wird."""
    detail_url = request.build_absolute_uri(
        reverse('jds_configurator:admin_feature_request_detail', args=[feature_request.pk])
    )
    subject = f"Neuer Funktionswunsch {feature_request.reference} - {feature_request.first_name} {feature_request.last_name}"
    message = (
        f"Neue Anfrage für eine individuelle Zusatzfunktion:\n\n"
        f"{feature_request.first_name} {feature_request.last_name} ({feature_request.email})\n"
        f"{feature_request.company_name}\n"
        f"Telefon: {feature_request.phone or '-'}\n\n"
        f"Beschreibung:\n{feature_request.description}\n\n"
        f"Zur Prüfung: {detail_url}"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.SUPPORT_EMAIL], fail_silently=False)
    except Exception:
        pass

    try:
        from JoelDigitalsApp.services.push import send_push_notification
        User = get_user_model()
        staff_ids = list(User.objects.filter(is_staff=True, is_active=True).values_list('id', flat=True))
        send_push_notification(
            title="Neuer Funktionswunsch",
            message=f"{feature_request.first_name} {feature_request.last_name}: {feature_request.description[:80]}",
            user_ids=staff_ids,
            url=detail_url,
        )
    except Exception:
        pass


@require_POST
def submit_feature_request(request):
    # Eigene Feldnamen (feature_*), da dasselbe <form> im Wizard auch die
    # Angebots-Kundendaten (first_name/last_name/...) enthält.
    first_name = request.POST.get('feature_first_name', '').strip()
    last_name = request.POST.get('feature_last_name', '').strip()
    email = request.POST.get('feature_email', '').strip()
    phone = request.POST.get('feature_phone', '').strip()
    company_name = request.POST.get('feature_company_name', '').strip()
    description = request.POST.get('feature_description', '').strip()

    if not first_name or not last_name or not email or not description:
        messages.error(request, "Bitte Name, E-Mail und eine Beschreibung der gewünschten Funktion angeben.")
        return redirect('jds_configurator:wizard')

    feature_request = JdsFeatureRequest.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_name=company_name,
        description=description,
    )
    _notify_staff_of_feature_request(feature_request, request)

    return render(request, 'jds_configurator/feature_request_thanks.html', {'feature_request': feature_request})
