import markdown
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404, redirect
from .models import Wiki
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from bs4 import BeautifulSoup  # NEU

def is_developer(user):
    return user.groups.filter(name='Entwickler').exists()

def get_language(request):
    return request.session.get('wiki_language', 'en')

# Sprache setzen und zur Übersicht weiterleiten
def set_language(request, lang):
    if lang in ['de', 'en', 'fr']:
        request.session['wiki_language'] = lang
    return redirect('wiki:overview')


# Wiki-Übersicht anzeigen
def wiki_overview(request):
    lang = get_language(request)
    
    # Alle öffentlichen Wikis für die gewählte Sprache
    wikis = Wiki.objects.filter(language=lang, is_developer_only=False)

    # Entwickler sehen zusätzlich ihre internen Wikis
    if request.user.is_authenticated and is_developer(request.user):
        wikis |= Wiki.objects.filter(language=lang, is_developer_only=True)

    return render(request, 'wiki/overview.html', {
        'wikis': wikis,
        'language': lang
    })


# Detailansicht eines Wiki-Eintrags
@login_required
def wiki_detail(request, slug):
    lang = get_language(request)
    wiki = get_object_or_404(Wiki, slug=slug)

    if wiki.language != lang:
        return HttpResponseForbidden("Diese Seite ist nicht in der gewählten Sprache verfügbar.")
    if wiki.is_developer_only and not is_developer(request.user):
        return HttpResponseForbidden("Nur für Entwickler zugänglich.")

    # Markdown → HTML mit IDs für h2/h3
    md = markdown.Markdown(extensions=['toc', 'fenced_code', 'attr_list'])
    content_html = md.convert(wiki.content)
    soup = BeautifulSoup(content_html, "html.parser")

    # Inhaltsverzeichnis generieren aus h2 und h3
    toc = []
    for tag in soup.find_all(['h2', 'h3']):
        text = tag.get_text()
        anchor = slugify(text)
        tag['id'] = anchor
        toc.append({'text': text, 'anchor': anchor, 'level': tag.name})

    return render(request, 'wiki/detail.html', {
        'wiki': wiki,
        'content_html': mark_safe(str(soup)),
        'toc': toc,
    })