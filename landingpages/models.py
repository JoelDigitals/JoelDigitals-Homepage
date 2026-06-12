from django.db import models
from django.utils.translation import gettext_lazy as _
class LandingPage(models.Model):
    LAYOUT_CHOICES = [
        ('default', 'Default – Purple Gradient'),
        ('minimal', 'Minimal – Clean White'),
        ('showcase', 'Showcase – Dark Product'),
        ('cards', 'Cards – Grid Layout'),
        ('dark-hero', 'Dark Hero – Bold Dark'),
        ('split', 'Split Screen – Left/Right'),
        ('magazine', 'Magazine – Content Heavy'),
        ('landing', 'Landing – Form Focus'),
    ]

    slug = models.SlugField(unique=True, help_text="URL slug, z.B. 'about-us'")
    is_active = models.BooleanField(default=True)

    # Layout & Design (online konfigurierbar)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='default',
                              verbose_name="Layout-Vorlage")
    custom_css = models.TextField(blank=True, verbose_name="Eigenes CSS",
                                  help_text="CSS-Regeln, die auf diese Seite angewendet werden")
    color_primary = models.CharField(max_length=7, default='#6366f1', verbose_name="Primärfarbe",
                                     help_text="Hex-Farbe, z.B. #6366f1")
    color_accent = models.CharField(max_length=7, default='#a855f7', verbose_name="Akzentfarbe",
                                    help_text="Hex-Farbe, z.B. #a855f7")

    # Übersetzbare Inhalte
    title_de = models.CharField(max_length=200, verbose_name="Titel Deutsch")
    title_en = models.CharField(max_length=200, verbose_name="Titel Englisch")

    subheadline_de = models.TextField(blank=True, verbose_name="Unterüberschrift Deutsch")
    subheadline_en = models.TextField(blank=True, verbose_name="Unterüberschrift Englisch")

    # Landing Page Haupttext – rohes HTML (wird 1:1 ausgegeben)
    content_de = models.TextField(verbose_name="HTML-Inhalt Deutsch", blank=True,
                                   help_text="Vollständiges HTML für den Seiteninhalt. Wird 1:1 ausgegeben.")
    content_en = models.TextField(verbose_name="HTML-Inhalt Englisch", blank=True,
                                   help_text="Full HTML for the page content. Output as-is.")

    cta_text_de = models.CharField(max_length=100, blank=True, verbose_name="CTA Text Deutsch")
    cta_link_de = models.URLField(blank=True, verbose_name="CTA Link Deutsch")

    cta_text_en = models.CharField(max_length=100, blank=True, verbose_name="CTA Text Englisch")
    cta_link_en = models.URLField(blank=True, verbose_name="CTA Link Englisch")

    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug
