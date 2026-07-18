# jds_configurator/views.py
import json
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from shop_ourapps.models import DiscountCode
from .models import JdsModule, JdsConfigRequest


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


def _get_discount_code(request):
    code_str = request.POST.get('discount_code', '').strip()
    if not code_str:
        return None
    code = DiscountCode.objects.filter(code__iexact=code_str).first()
    if code:
        code.update_status()
        if code.is_valid_now():
            return code
    return None


def wizard(request):
    core_modules = JdsModule.objects.filter(is_core=True, is_active=True)
    addon_modules = JdsModule.objects.filter(is_core=False, is_active=True)
    categories = {}
    for m in addon_modules:
        categories.setdefault(m.category, []).append(m)
    category_labels = dict(JdsModule.CATEGORY_CHOICES)

    return render(request, 'jds_configurator/wizard.html', {
        'core_modules': core_modules,
        'categories': [
            {'key': key, 'label': category_labels.get(key, key), 'modules': mods}
            for key, mods in categories.items()
        ],
        'basismodul_price': JdsConfigRequest.BASISMODUL_PRICE,
    })


@csrf_exempt
def validate_discount(request):
    if request.method != 'POST':
        return JsonResponse({'valid': False}, status=405)
    data = json.loads(request.body or '{}')
    code_str = (data.get('code') or '').strip()
    if not code_str:
        return JsonResponse({'valid': False, 'message': 'Kein Code angegeben.'})
    code = DiscountCode.objects.filter(code__iexact=code_str).first()
    if not code:
        return JsonResponse({'valid': False, 'message': 'Rabattcode nicht gefunden.'})
    code.update_status()
    if not code.is_valid_now():
        return JsonResponse({'valid': False, 'message': 'Rabattcode ist ungültig oder abgelaufen.'})
    return JsonResponse({'valid': True, 'percentage': float(code.percentage)})


def _build_offer_context(request):
    customer = _customer_fields(request)
    addon_modules = list(_selected_modules(request))
    discount_code = _get_discount_code(request)

    subtotal = JdsConfigRequest.BASISMODUL_PRICE + sum((m.monthly_price for m in addon_modules), Decimal('0.00'))
    discount_amount = Decimal('0.00')
    if discount_code:
        discount_amount = (subtotal * discount_code.percentage / Decimal('100')).quantize(Decimal('0.01'))
    total = max(Decimal('0.00'), subtotal - discount_amount)

    return {
        'customer': customer,
        'addon_modules': addon_modules,
        'discount_code': discount_code,
        'basismodul_price': JdsConfigRequest.BASISMODUL_PRICE,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
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
    discount_code = _get_discount_code(request)

    config_request = JdsConfigRequest.objects.create(**customer, discount_code=discount_code)
    config_request.modules.set(addon_modules)
    config_request.recalculate_totals(discount_code=discount_code)
    config_request.save()

    return render(request, 'jds_configurator/thanks.html', {'config_request': config_request})
