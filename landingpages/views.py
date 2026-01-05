from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from .models import LandingPage

def landing_page_view(request, slug):
    page = get_object_or_404(LandingPage, slug=slug, is_active=True)
    lang = get_language()[:2]  # 'de' oder 'en'

    # Felder nach Sprache auswählen
    title = getattr(page, f"title_{lang}", page.title_de)
    subheadline = getattr(page, f"subheadline_{lang}", page.subheadline_de)
    content = getattr(page, f"content_{lang}", page.content_de)
    cta_text = getattr(page, f"cta_text_{lang}", page.cta_text_de)
    cta_link = getattr(page, f"cta_link_{lang}", page.cta_link_de)

    return render(request, "landingpages/page.html", {
        "page": page,
        "title": title,
        "subheadline": subheadline,
        "content": content,
        "cta_text": cta_text,
        "cta_link": cta_link,
    })
