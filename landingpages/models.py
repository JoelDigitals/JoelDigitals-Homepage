from django.db import models
from django.utils.translation import gettext_lazy as _

class LandingPage(models.Model):
    slug = models.SlugField(unique=True, help_text="URL slug, z.B. 'about-us'")
    is_active = models.BooleanField(default=True)

    # Übersetzbare Inhalte
    title_de = models.CharField(max_length=200, verbose_name="Titel Deutsch")
    title_en = models.CharField(max_length=200, verbose_name="Titel Englisch")

    subheadline_de = models.TextField(blank=True, verbose_name="Unterüberschrift Deutsch")
    subheadline_en = models.TextField(blank=True, verbose_name="Unterüberschrift Englisch")

    # Landing Page Haupttext mit HTML/Style
    content_de = models.TextField(verbose_name="Landing Page Text Deutsch", blank=True)
    content_en = models.TextField(verbose_name="Landing Page Text Englisch", blank=True)

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
