from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import LandingPage

TEMPLATE_MAP = {
    'default': 'landingpages/page_default.html',
    'minimal': 'landingpages/page_minimal.html',
    'showcase': 'landingpages/page_showcase.html',
    'cards': 'landingpages/page_cards.html',
    'dark-hero': 'landingpages/page_dark_hero.html',
    'split': 'landingpages/page_split.html',
    'magazine': 'landingpages/page_magazine.html',
    'landing': 'landingpages/page_landing.html',
}

def landing_page_view(request, slug):
    page = get_object_or_404(LandingPage, slug=slug, is_active=True)
    lang = get_language()[:2]

    if request.method == 'POST' and page.layout == 'landing':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            subject = f'Anfrage von {name} – {page.title_de}'
            body = f"Name: {name}\nE-Mail: {email}\nSeite: {page.title_de} ({request.build_absolute_uri()})\n\nNachricht:\n{message}"
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.COMPANY_EMAIL])
                messages.success(request, 'Vielen Dank! Wir melden uns innerhalb von 24 Stunden bei Ihnen.')
            except Exception:
                messages.error(request, 'Beim Senden ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.')
        else:
            messages.error(request, 'Bitte füllen Sie alle Pflichtfelder aus.')

    template = TEMPLATE_MAP.get(page.layout, 'landingpages/page_default.html')

    title = getattr(page, f"title_{lang}", page.title_de)
    subheadline = getattr(page, f"subheadline_{lang}", page.subheadline_de)
    content = getattr(page, f"content_{lang}", page.content_de)
    cta_text = getattr(page, f"cta_text_{lang}", page.cta_text_de)
    cta_link = getattr(page, f"cta_link_{lang}", page.cta_link_de)

    return render(request, template, {
        "page": page,
        "title": title,
        "subheadline": subheadline,
        "content": content,
        "cta_text": cta_text,
        "cta_link": cta_link,
        "seo_title": page.seo_title,
        "seo_description": page.seo_description,
        "custom_css": page.custom_css,
        "color_primary": page.color_primary,
        "color_accent": page.color_accent,
        "lang": lang,
    })
