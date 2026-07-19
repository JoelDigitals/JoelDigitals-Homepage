# jds_configurator/admin_views.py
# Genehmigungs-Oberfläche für "Dein individuelles JDS Management"-Anfragen.
# Nur für Plattform-Admins (is_staff) - kein Self-Service für normale Kunden.
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from django.contrib.auth import get_user_model

from shop_ourapps.models import Order, OrderItem
from .models import JdsConfigRequest, JdsFeatureRequest, extra_users_total


@staff_member_required
def request_list(request):
    requests = JdsConfigRequest.objects.all().order_by('status', '-created_at')
    return render(request, 'jds_configurator/admin/request_list.html', {'requests': requests})


@staff_member_required
def request_detail(request, pk):
    config_request = get_object_or_404(JdsConfigRequest, pk=pk)
    return render(request, 'jds_configurator/admin/request_detail.html', {'config_request': config_request})


@staff_member_required
def request_approve(request, pk):
    """Genehmigt eine Anfrage: legt einen echten Order + OrderItems im bestehenden
    Shop-System an (ein Item pro gewähltem Modul, per name_override statt eines
    App/Package-Katalogeintrags), damit PDF-Rechnung und Zahlungsabwicklung die
    vorhandene Logik nutzen. Legt KEIN JDS-Management-Team an - das bleibt manuell
    nach Zahlungseingang."""
    config_request = get_object_or_404(JdsConfigRequest, pk=pk)

    if request.method == 'POST':
        if config_request.status != 'pending':
            messages.error(request, "Diese Anfrage wurde bereits bearbeitet.")
            return redirect('jds_configurator:admin_request_detail', pk=pk)

        payment_method = request.POST.get('payment_method')
        if payment_method not in dict(JdsConfigRequest.PAYMENT_CHOICES):
            messages.error(request, "Bitte eine Zahlungsart auswählen.")
            return redirect('jds_configurator:admin_request_detail', pk=pk)

        # WICHTIG: Die Bestellung gehoert dem Kunden, nicht dem genehmigenden
        # Admin - sonst taucht sie faelschlich in dessen eigenem "Meine
        # Bestellungen"/App-Bestellungen-Tab auf. JdsConfigRequest hat kein
        # eigenes user-FK (Formular ist ohne Login ausfuellbar), daher per
        # E-Mail nach einem bestehenden Konto suchen.
        User = get_user_model()
        customer_user = User.objects.filter(email__iexact=config_request.email).first()
        if not customer_user:
            messages.error(
                request,
                f"Kein Benutzerkonto mit der E-Mail {config_request.email} gefunden. "
                f"Der Kunde muss sich zuerst registrieren, oder nutze 'Neue Bestellung' im Bestellungen-Admin, "
                f"um die Bestellung manuell mit Benutzerauswahl anzulegen."
            )
            return redirect('jds_configurator:admin_request_detail', pk=pk)

        order = Order.objects.create(
            user=customer_user,
            first_name=config_request.first_name,
            last_name=config_request.last_name,
            email=config_request.email,
            address=config_request.address,
            zip_code=config_request.zip_code,
            city=config_request.city,
            phone=config_request.phone,
            company_name=config_request.company_name,
            vat_number=config_request.vat_number,
            payment_method='PayPal' if payment_method == 'paypal' else 'Überweisung',
            status='Received',
            subtotal=config_request.total_amount,
            total_amount=config_request.total_amount,
        )
        OrderItem.objects.create(
            order=order,
            name_override=f"JDS Management Basismodul (inkl. TeamPage, Arbeitszeiten, Rollenverwaltung, Rechnungen u.v.m.)",
            quantity=1,
            single_price=JdsConfigRequest.BASISMODUL_PRICE,
            discount_price=JdsConfigRequest.BASISMODUL_PRICE,
            price=JdsConfigRequest.BASISMODUL_PRICE,
        )
        for module in config_request.addon_modules:
            OrderItem.objects.create(
                order=order,
                name_override=f"JDS Management Modul: {module.name}",
                quantity=1,
                single_price=module.price,
                discount_price=module.price,
                price=module.price,
            )
        if config_request.extra_users:
            users_price = extra_users_total(config_request.extra_users)
            OrderItem.objects.create(
                order=order,
                name_override=f"JDS Management: {config_request.extra_users} zusätzliche User",
                quantity=1,
                single_price=users_price,
                discount_price=users_price,
                price=users_price,
            )

        config_request.status = 'approved'
        config_request.payment_method = payment_method
        config_request.order = order
        config_request.reviewed_at = timezone.now()
        config_request.reviewed_by = request.user
        config_request.save()

        messages.success(request, f"Anfrage genehmigt. Order #{order.id} wurde angelegt.")
        return redirect('jds_configurator:admin_request_detail', pk=pk)

    return redirect('jds_configurator:admin_request_detail', pk=pk)


@staff_member_required
def request_reject(request, pk):
    config_request = get_object_or_404(JdsConfigRequest, pk=pk)
    if request.method == 'POST':
        if config_request.status != 'pending':
            messages.error(request, "Diese Anfrage wurde bereits bearbeitet.")
            return redirect('jds_configurator:admin_request_detail', pk=pk)
        config_request.status = 'rejected'
        config_request.internal_notes = request.POST.get('internal_notes', config_request.internal_notes)
        config_request.reviewed_at = timezone.now()
        config_request.reviewed_by = request.user
        config_request.save()
        messages.success(request, "Anfrage abgelehnt.")
    return redirect('jds_configurator:admin_request_detail', pk=pk)


# ─────────────────────────────────────────────────────────────────────────
# Individuelle Funktionswünsche (JdsFeatureRequest) - keine Bestellung,
# nur eine Anfrage zur manuellen Prüfung/individuellen Entwicklung.
# ─────────────────────────────────────────────────────────────────────────

def _notify_feature_request_customer(feature_request, status):
    if status == 'approved':
        subject = f"Deine Funktionswunsch-Anfrage {feature_request.reference} wurde genehmigt"
        message = (
            f"Hallo {feature_request.first_name},\n\n"
            f"gute Nachrichten: Wir haben deinen Funktionswunsch geprüft und werden ihn umsetzen.\n\n"
            f"Voraussichtliche Verfügbarkeit: {feature_request.estimated_availability or 'in Kürze'}\n\n"
            f"Bei Rückfragen melden wir uns bei dir per E-Mail oder Telefon.\n\n"
            f"Viele Grüße\nJoel Digitals"
        )
    else:
        subject = f"Deine Funktionswunsch-Anfrage {feature_request.reference}"
        message = (
            f"Hallo {feature_request.first_name},\n\n"
            f"vielen Dank für deine Anfrage zu einer individuellen Funktion. Nach Prüfung können wir "
            f"diese aktuell leider nicht umsetzen.\n\n"
            f"Viele Grüße\nJoel Digitals"
        )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [feature_request.email], fail_silently=False)
    except Exception:
        return False
    return True


@staff_member_required
def feature_request_list(request):
    requests = JdsFeatureRequest.objects.all().order_by('status', '-created_at')
    return render(request, 'jds_configurator/admin/feature_request_list.html', {'requests': requests})


@staff_member_required
def feature_request_detail(request, pk):
    feature_request = get_object_or_404(JdsFeatureRequest, pk=pk)
    return render(request, 'jds_configurator/admin/feature_request_detail.html', {'feature_request': feature_request})


@staff_member_required
def feature_request_approve(request, pk):
    feature_request = get_object_or_404(JdsFeatureRequest, pk=pk)
    if request.method == 'POST':
        if feature_request.status in ('approved', 'rejected'):
            messages.error(request, "Diese Anfrage wurde bereits abschließend bearbeitet.")
            return redirect('jds_configurator:admin_feature_request_detail', pk=pk)

        estimated_availability = request.POST.get('estimated_availability', '').strip()
        if not estimated_availability:
            messages.error(request, "Bitte eine voraussichtliche Verfügbarkeit angeben.")
            return redirect('jds_configurator:admin_feature_request_detail', pk=pk)

        feature_request.status = 'approved'
        feature_request.estimated_availability = estimated_availability
        feature_request.internal_notes = request.POST.get('internal_notes', feature_request.internal_notes)
        feature_request.reviewed_at = timezone.now()
        feature_request.reviewed_by = request.user
        feature_request.save()

        if _notify_feature_request_customer(feature_request, 'approved'):
            messages.success(request, "Anfrage genehmigt, Kunde wurde per E-Mail benachrichtigt.")
        else:
            messages.warning(request, "Anfrage genehmigt, aber die Benachrichtigungs-E-Mail konnte nicht gesendet werden.")
        return redirect('jds_configurator:admin_feature_request_detail', pk=pk)

    return redirect('jds_configurator:admin_feature_request_detail', pk=pk)


@staff_member_required
def feature_request_reject(request, pk):
    feature_request = get_object_or_404(JdsFeatureRequest, pk=pk)
    if request.method == 'POST':
        if feature_request.status in ('approved', 'rejected'):
            messages.error(request, "Diese Anfrage wurde bereits abschließend bearbeitet.")
            return redirect('jds_configurator:admin_feature_request_detail', pk=pk)

        feature_request.status = 'rejected'
        feature_request.internal_notes = request.POST.get('internal_notes', feature_request.internal_notes)
        feature_request.reviewed_at = timezone.now()
        feature_request.reviewed_by = request.user
        feature_request.save()

        if _notify_feature_request_customer(feature_request, 'rejected'):
            messages.success(request, "Anfrage abgelehnt, Kunde wurde per E-Mail benachrichtigt.")
        else:
            messages.warning(request, "Anfrage abgelehnt, aber die Benachrichtigungs-E-Mail konnte nicht gesendet werden.")
    return redirect('jds_configurator:admin_feature_request_detail', pk=pk)


@staff_member_required
def feature_request_mark_in_review(request, pk):
    """Markiert eine Anfrage als 'In Prüfung', z.B. während Rückfragen per Mail/Telefon laufen."""
    feature_request = get_object_or_404(JdsFeatureRequest, pk=pk)
    if request.method == 'POST' and feature_request.status == 'pending':
        feature_request.status = 'in_review'
        feature_request.internal_notes = request.POST.get('internal_notes', feature_request.internal_notes)
        feature_request.save()
        messages.success(request, "Anfrage als 'In Prüfung' markiert.")
    return redirect('jds_configurator:admin_feature_request_detail', pk=pk)
