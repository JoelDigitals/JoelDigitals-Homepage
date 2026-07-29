from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import get_language, gettext as _
from .models import BackroomProduct, BackroomAccessRequest
from .access import has_backroom_access

def _localize(product, lang):
    product.display_name = product.name_english if (lang == 'en' and product.name_english) else product.name
    product.display_description = product.description_english if (lang == 'en' and product.description_english) else product.description
    return product

def product_list(request):
    if not has_backroom_access(request.user):
        return redirect('backroom_access_request')

    lang = get_language()
    products = BackroomProduct.objects.filter(is_published=True)

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(name_english__icontains=query) | Q(description_english__icontains=query)
        )

    sort = request.GET.get("sort", "order")
    sort_options = {
        "order": ["order", "name"],
        "name": ["name"],
        "price_asc": ["price"],
        "price_desc": ["-price"],
        "newest": ["-created_at"],
    }
    ordering = sort_options.get(sort, ["order", "name"])
    products = list(products.order_by(*ordering))
    for product in products:
        _localize(product, lang)

    return render(request, 'backroom/product_list.html', {
        'products': products,
        'product_count': len(products),
        'query': query,
        'current_sort': sort,
        'lang': lang,
    })

def product_detail(request, slug):
    if not has_backroom_access(request.user):
        return redirect('backroom_access_request')

    lang = get_language()
    product = get_object_or_404(BackroomProduct, slug=slug, is_published=True)
    _localize(product, lang)
    return render(request, 'backroom/product_detail.html', {
        'product': product,
        'lang': lang,
    })


@login_required
def access_request(request):
    existing = BackroomAccessRequest.objects.filter(user=request.user).order_by('-created_at').first()

    if request.method == 'POST':
        if existing and existing.status in ('pending', 'approved'):
            messages.info(request, _("Du hast bereits eine Anfrage laufen."))
            return redirect('backroom_access_request')

        message = request.POST.get('message', '').strip()
        BackroomAccessRequest.objects.create(user=request.user, message=message)
        messages.success(request, _("Deine Anfrage wurde eingereicht. Wir melden uns, sobald sie geprüft wurde."))
        return redirect('backroom_access_request')

    return render(request, 'backroom/access_request.html', {
        'existing_request': existing,
        'has_access': has_backroom_access(request.user),
    })
