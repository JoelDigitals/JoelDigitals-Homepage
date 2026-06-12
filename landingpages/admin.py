from django.contrib import admin
from django import forms
from django.db import models
from .models import LandingPage


HTML_TEXTAREA = forms.Textarea(attrs={
    'rows': 25,
    'style': 'font-family:ui-monospace,SFMono-Regular,Consolas,monospace;width:100%;font-size:13px;tab-size:2',
})


class LandingPageAdminForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = '__all__'
        widgets = {
            'content_de': HTML_TEXTAREA,
            'content_en': HTML_TEXTAREA,
            'custom_css': forms.Textarea(attrs={'rows': 10, 'style': 'font-family:monospace;width:100%'}),
        }


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    form = LandingPageAdminForm
    list_display = ['slug', 'layout', 'is_active', 'title_de', 'title_en', 'created_at', 'updated_at']
    list_filter = ['is_active', 'layout']
    search_fields = ['slug', 'title_de', 'title_en']
    prepopulated_fields = {'slug': ('title_de',)}
    fieldsets = [
        ('Allgemein', {'fields': ['slug', 'is_active', 'layout']}),
        ('Design (online konfigurierbar)', {'fields': ['custom_css', 'color_primary', 'color_accent'],
                                             'classes': ['wide']}),
        ('Inhalt Deutsch', {'fields': ['title_de', 'subheadline_de', 'content_de',
                                        'cta_text_de', 'cta_link_de']}),
        ('Inhalt Englisch', {'fields': ['title_en', 'subheadline_en', 'content_en',
                                        'cta_text_en', 'cta_link_en']}),
        ('SEO', {'fields': ['seo_title', 'seo_description']}),
    ]
