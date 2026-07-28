# website_configurator/admin_views.py
# Review-Oberfläche für Website-Konfigurator-Leads. Nur für Plattform-Admins
# (is_staff) - keine Selbstbedienung für Kunden, kein automatischer Kaufvorgang
# wie bei jds_configurator (das hier ist eine Anfrage, keine Bestellung).
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailTemplate, WebsiteConfigRequest

ARCHIVED_STATUSES = ['won', 'lost']


def _in_app(request):
    return getattr(request, 'base_template', None) == 'base_app.html'


def _redirect_to_detail(request, pk):
    if _in_app(request):
        return redirect('jd_website_config_detail_app', pk=pk)
    return redirect('website_configurator:admin_request_detail', pk=pk)


@staff_member_required
def request_list(request):
    """Aktive Anfragen (alles außer 'Gewonnen'/'Verloren' - die landen im Archiv)."""
    requests = WebsiteConfigRequest.objects.exclude(status__in=ARCHIVED_STATUSES).order_by('status', '-created_at')
    return render(request, 'website_configurator/admin/request_list.html', {'requests': requests})


@staff_member_required
def request_archive(request):
    query = request.GET.get('q', '').strip()
    archived = WebsiteConfigRequest.objects.filter(status__in=ARCHIVED_STATUSES)
    if query:
        archived = archived.filter(
            Q(reference__icontains=query) | Q(name__icontains=query) |
            Q(email__icontains=query) | Q(company_name__icontains=query)
        )
    paginator = Paginator(archived.order_by('-updated_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'website_configurator/admin/request_archive.html', {'page_obj': page_obj, 'query': query})


@staff_member_required
def request_detail(request, pk):
    config_request = get_object_or_404(WebsiteConfigRequest, pk=pk)
    return render(request, 'website_configurator/admin/request_detail.html', {'config_request': config_request})


@staff_member_required
def request_update_status(request, pk):
    config_request = get_object_or_404(WebsiteConfigRequest, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status not in dict(WebsiteConfigRequest.STATUS_CHOICES):
            messages.error(request, "Ungültiger Status.")
            return _redirect_to_detail(request, pk)
        config_request.status = status
        config_request.internal_notes = request.POST.get('internal_notes', config_request.internal_notes)
        config_request.reviewed_at = timezone.now()
        config_request.reviewed_by = request.user
        config_request.save()
        messages.success(request, "Status aktualisiert.")
    return _redirect_to_detail(request, pk)


class _SafeFormatDict(dict):
    """Lässt {platzhalter} unbekannter Vorlagen-Keys als leeren String
    verschwinden statt einen KeyError zu werfen (str.format_map)."""
    def __missing__(self, key):
        return ''


def _template_placeholders(config_request):
    return _SafeFormatDict({
        'name': config_request.name,
        'reference': config_request.reference,
        'company_name': config_request.company_name or '',
        'site_type': config_request.get_site_type_display() or '',
        'tech': config_request.get_tech_display() or '',
        'estimated_total': f"{config_request.estimated_total} €" if config_request.estimated_total is not None else "Preis auf Anfrage",
    })


@staff_member_required
def request_send_mail(request, pk):
    """Freitext-Mail an den Interessenten - anders als die automatischen
    Benachrichtigungen (submit_request) hier frei formulierbar, fuer
    individuelle Rückfragen/Angebote durch den Vertrieb. Versendet als
    gestaltete HTML-Mail (emails/staff_mail.html) mit Text-Fallback.
    'Vorlagen' (EmailTemplate) koennen ueber ein Dropdown vorausgefuellt
    werden - Platzhalter wie {name}/{reference} werden serverseitig schon
    beim Laden der Seite fuer JEDE Vorlage ersetzt (siehe templates_json)."""
    config_request = get_object_or_404(WebsiteConfigRequest, pk=pk)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        if not subject or not message:
            messages.error(request, "Bitte Betreff und Nachricht angeben.")
        else:
            try:
                html_content = render_to_string('website_configurator/emails/staff_mail.html', {
                    'subject': subject,
                    'message': message,
                    'config_request': config_request,
                    'now': timezone.now(),
                })
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[config_request.email],
                    reply_to=[settings.SUPPORT_EMAIL],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                messages.success(request, f"E-Mail an {config_request.email} gesendet.")
                return _redirect_to_detail(request, pk)
            except Exception as e:
                messages.error(request, f"E-Mail konnte nicht gesendet werden: {e}")

    placeholders = _template_placeholders(config_request)
    default_subject = f"Deine Website-Anfrage {config_request.reference}"
    default_message = f"Hallo {config_request.name},\n\n\n\nViele Grüße\nJoel Digitals"

    templates_json = json.dumps([
        {
            'id': t.id,
            'name': t.name,
            'subject': t.subject.format_map(placeholders),
            'message': t.body.format_map(placeholders),
        }
        for t in EmailTemplate.objects.filter(is_active=True)
    ])

    return render(request, 'website_configurator/admin/request_send_mail.html', {
        'config_request': config_request,
        'default_subject': request.POST.get('subject', default_subject),
        'default_message': request.POST.get('message', default_message),
        'templates_json': templates_json,
    })
