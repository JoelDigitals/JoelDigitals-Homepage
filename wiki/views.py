import markdown
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404, redirect
from .models import Wiki
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from bs4 import BeautifulSoup  # NEU
from collections import defaultdict

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

    # Nur veröffentlichte öffentliche Wikis für die gewählte Sprache
    wikis = Wiki.objects.filter(language=lang, is_developer_only=False, is_published=True)

    # Entwickler sehen zusätzlich veröffentlichte interne Wikis
    if request.user.is_authenticated and is_developer(request.user):
        dev_wikis = Wiki.objects.filter(language=lang, is_developer_only=True, is_published=True)
        wikis = wikis | dev_wikis  # Union der QuerySets

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

    # Markdown → HTML
    md = markdown.Markdown(extensions=['toc', 'fenced_code', 'attr_list'])
    content_html = md.convert(wiki.content)
    soup = BeautifulSoup(content_html, "html.parser")

    # Eindeutige Anker erzeugen
    ids = defaultdict(int)
    toc = []

    for tag in soup.find_all(['h2', 'h3']):
        text = tag.get_text()
        base_id = slugify(text)
        ids[base_id] += 1
        anchor = base_id if ids[base_id] == 1 else f"{base_id}-{ids[base_id]}"
        tag['id'] = anchor
        toc.append({'text': text, 'anchor': anchor, 'level': tag.name})

    # Alle inline-Styles aus CKEditor entfernen (weiße Schrift auf weißem Grund)
    for tag in soup.find_all(style=True):
        del tag['style']

    # Auch bgcolor- und color-Attribute entfernen
    for tag in soup.find_all(bgcolor=True):
        del tag['bgcolor']
    for tag in soup.find_all(color=True):
        del tag['color']

    return render(request, 'wiki/detail.html', {
        'wiki': wiki,
        'content_html': mark_safe(str(soup)),
        'toc': toc,
    })