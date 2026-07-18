# jds_configurator/admin_views.py
# Genehmigungs-Oberfläche für "Dein individuelles JDS Management"-Anfragen.
# Nur für Plattform-Admins (is_staff) - kein Self-Service für normale Kunden.
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from shop_ourapps.models import Order, OrderItem
from .models import JdsConfigRequest


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

        order = Order.objects.create(
            user=request.user,
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
            subtotal=config_request.subtotal,
            discount_amount=config_request.discount_amount,
            total_amount=config_request.total_amount,
            discount_code=config_request.discount_code,
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
                single_price=module.monthly_price,
                discount_price=module.monthly_price,
                price=module.monthly_price,
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
