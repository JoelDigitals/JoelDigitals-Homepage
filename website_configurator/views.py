# website_configurator/views.py
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from .models import BasePricingOption, ConfiguratorFeature, WebsiteConfigRequest, calculate_totals


def configurator_context():
    features = ConfiguratorFeature.objects.filter(is_active=True)
    categories = {}
    for f in features:
        categories.setdefault(f.category, []).append(f)
    category_labels = dict(ConfiguratorFeature.CATEGORY_CHOICES)

    tech_options = [
        {'value': value, 'label': label, 'site_types': BasePricingOption.TECH_SITE_TYPES.get(value, 'onepager,multipage,shop')}
        for value, label in BasePricingOption.TECH_CHOICES
    ]

    return {
        'site_types': BasePricingOption.SITE_TYPE_CHOICES,
        'tech_options': tech_options,
        'base_options': BasePricingOption.objects.filter(is_active=True),
        'categories': [
            {'key': key, 'label': category_labels.get(key, key), 'features': feats}
            for key, feats in categories.items()
        ],
    }


def wizard(request):
    return render(request, 'website_configurator/wizard.html', configurator_context())


def _contact_fields(request):
    return {
        'name': request.POST.get('name', '').strip(),
        'email': request.POST.get('email', '').strip(),
        'phone': request.POST.get('phone', '').strip(),
        'company_name': request.POST.get('company_name', '').strip(),
    }


def _selected_features(request):
    keys = request.POST.getlist('features')
    return ConfiguratorFeature.objects.filter(key__in=keys, is_active=True)


def _page_count(request, site_type):
    if site_type != 'multipage':
        return None
    try:
        return max(1, int(request.POST.get('page_count', 5)))
    except (TypeError, ValueError):
        return 5


@require_POST
def save_contact(request):
    """Schritt 1 des Wizards: legt den Lead sofort mit den Kontaktdaten als
    'draft' an, damit er auch bei Abbruch der weiteren Schritte fürs
    Vertriebsteam sichtbar bleibt. Liefert die ID zurück, die der Client in
    einem Hidden-Feld hält und bei den folgenden Schritten mitschickt."""
    contact = _contact_fields(request)
    if not contact['name'] or not contact['email'] or not contact['phone']:
        return JsonResponse({'error': 'missing_fields'}, status=400)

    config_request = WebsiteConfigRequest.objects.create(status='draft', **contact)
    return JsonResponse({'id': config_request.pk, 'reference': config_request.reference})


@require_POST
def update_draft(request, pk):
    """Wird nach jedem weiteren Wizard-Schritt (Website-Typ, Umsetzung,
    Features) per AJAX aufgerufen, um den Fortschritt serverseitig zu
    sichern. Nur solange der Lead noch 'draft' ist - ist er bereits final
    abgesendet, wird er über diesen Endpunkt nicht mehr verändert."""
    config_request = get_object_or_404(WebsiteConfigRequest, pk=pk, status='draft')

    site_type = request.POST.get('site_type')
    if site_type in dict(BasePricingOption.SITE_TYPE_CHOICES):
        config_request.site_type = site_type

    tech = request.POST.get('tech')
    if tech in dict(BasePricingOption.TECH_CHOICES):
        config_request.tech = tech

    if 'page_count' in request.POST:
        config_request.page_count = _page_count(request, config_request.site_type)

    if 'features_step' in request.POST:
        config_request.features.set(_selected_features(request))

    if 'message' in request.POST:
        config_request.message = request.POST.get('message', '').strip()

    config_request.recalculate_totals()
    config_request.save()

    return JsonResponse({
        'ok': True,
        'estimated_total': str(config_request.estimated_total) if config_request.estimated_total is not None else None,
    })


def _notify_staff(config_request, request):
    """Benachrichtigt das Vertriebsteam per Mail + Push (Warteschlange) über eine
    neue Website-Anfrage - Muster analog contact.views.appointment_create
    (PendingPush an die Gruppe 'Selling', vom 5-Minuten-Cron gesammelt verschickt)."""
    detail_url = request.build_absolute_uri(
        reverse('website_configurator:admin_request_detail', args=[config_request.pk])
    )
    price_text = f"{config_request.estimated_total} €" if config_request.estimated_total is not None else "Preis auf Anfrage"
    subject = f"Neuer verbindlicher Website-Auftrag {config_request.reference} - {config_request.name}"
    message = (
        f"Neuer VERBINDLICHER Auftrag über den Website-Konfigurator (AGB/Datenschutz akzeptiert am "
        f"{config_request.terms_accepted_at:%d.%m.%Y %H:%M} Uhr):\n\n"
        f"{config_request.name} ({config_request.email})\n"
        f"{config_request.company_name}\n"
        f"Telefon: {config_request.phone or '-'}\n\n"
        f"Typ: {config_request.get_site_type_display()}\n"
        f"Umsetzung: {config_request.get_tech_display()}\n"
        f"Geschätzter Preis: {price_text}\n\n"
        f"Nachricht:\n{config_request.message or '-'}\n\n"
        f"Zur Prüfung: {detail_url}"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.SUPPORT_EMAIL], fail_silently=False)
    except Exception:
        pass

    try:
        from django.contrib.auth import get_user_model
        from JoelDigitalsApp.models import PendingPush
        User = get_user_model()
        sales_staff_ids = list(
            User.objects.filter(groups__name='Selling').distinct().values_list('id', flat=True)
        )
        if sales_staff_ids:
            PendingPush.objects.create(
                title="Neuer verbindlicher Website-Auftrag",
                message=f"{config_request.name}: {config_request.get_site_type_display()} ({price_text})",
                user_ids=sales_staff_ids,
                url=detail_url,
            )
    except Exception:
        pass


def submit_request(request):
    """Finaler, VERBINDLICHER Absende-Schritt (Checkbox 'agb_accepted' im
    Formular bestätigt AGB/Datenschutz - anders als bei save_contact/
    update_draft/download_offer_pdf ist das hier keine unverbindliche
    Anfrage mehr, sondern die verbindliche Beauftragung). Da Kontaktdaten/
    Auswahl bereits schrittweise per update_draft gesichert wurden, wird -
    falls vorhanden - der bestehende Draft (request_id-Hidden-Feld)
    übernommen; ohne gültige Draft-ID (z.B. bei JS-Fehler) wird als Fallback
    direkt aus den kompletten POST-Daten ein neuer Datensatz angelegt, damit
    der Auftrag in jedem Fall ankommt."""
    if request.method != 'POST':
        return redirect('website_configurator:wizard')

    contact = _contact_fields(request)
    site_type = request.POST.get('site_type', '')
    tech = request.POST.get('tech', '')
    agb_accepted = request.POST.get('agb_accepted') == 'on'

    if not contact['name'] or not contact['email'] or not contact['phone'] or site_type not in dict(BasePricingOption.SITE_TYPE_CHOICES) or tech not in dict(BasePricingOption.TECH_CHOICES):
        messages.error(request, "Bitte Website-Typ, Umsetzung, Namen, Telefonnummer und E-Mail-Adresse angeben.")
        return redirect('website_configurator:wizard')

    if not agb_accepted:
        messages.error(request, "Bitte bestätige die AGB/Datenschutzbestimmungen, um den Auftrag verbindlich abzusenden.")
        return redirect('website_configurator:wizard')

    page_count = _page_count(request, site_type)
    message = request.POST.get('message', '').strip()
    features = _selected_features(request)

    request_id = request.POST.get('request_id')
    config_request = WebsiteConfigRequest.objects.filter(pk=request_id, status='draft').first() if request_id else None
    if config_request is None:
        config_request = WebsiteConfigRequest.objects.create(site_type=site_type, tech=tech, page_count=page_count, message=message, **contact)
    else:
        for field, value in contact.items():
            setattr(config_request, field, value)
        config_request.site_type = site_type
        config_request.tech = tech
        config_request.page_count = page_count
        config_request.message = message

    config_request.features.set(features)
    config_request.status = 'pending'
    config_request.terms_accepted = True
    config_request.terms_accepted_at = timezone.now()
    config_request.recalculate_totals()
    config_request.save()

    _notify_staff(config_request, request)

    return render(request, 'website_configurator/thanks.html', {'config_request': config_request})


def _offer_pdf_context(request):
    contact = _contact_fields(request)
    site_type = request.POST.get('site_type', '')
    tech = request.POST.get('tech', '')
    page_count = _page_count(request, site_type)
    features = list(_selected_features(request))
    base_option = BasePricingOption.objects.filter(site_type=site_type, tech=tech, is_active=True).first()
    total = calculate_totals(base_option, features, page_count or 0)

    extra_pages = 0
    if base_option and page_count and base_option.included_pages:
        extra_pages = max(0, page_count - base_option.included_pages)

    return {
        'contact': contact,
        'site_type_label': dict(BasePricingOption.SITE_TYPE_CHOICES).get(site_type, site_type),
        'tech_label': dict(BasePricingOption.TECH_CHOICES).get(tech, tech),
        'page_count': page_count,
        'extra_pages': extra_pages,
        'base_option': base_option,
        'features': features,
        'total': total,
    }


def download_offer_pdf(request):
    if request.method != 'POST':
        return redirect('website_configurator:wizard')

    context = _offer_pdf_context(request)
    context['now'] = timezone.now()

    html_string = render_to_string('website_configurator/offer_pdf.html', context)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_file, encoding='UTF-8')
    if pisa_status.err:
        return HttpResponse('Fehler beim Erstellen des Angebots-PDFs.', status=500)

    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Angebot_Website.pdf"'
    return response
