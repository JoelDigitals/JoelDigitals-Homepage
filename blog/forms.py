# blog/forms.py

from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import BlogPost, BlogCategory


class BlogPostForm(forms.ModelForm):
    content_de = forms.CharField(widget=CKEditorWidget(), label="Inhalt (DE)")
    content_en = forms.CharField(widget=CKEditorWidget(), label="Inhalt (EN)")

    class Meta:
        model = BlogPost
        fields = ['title_de', 'title_en', 'teaser_image', 'content_de', 'content_en', 'is_published', 'categories']
        labels = {
            'title_de': 'Titel (DE)',
            'title_en': 'Titel (EN)',
            'teaser_image': 'Teaser-Bild',
            'is_published': 'Veröffentlicht?',
            'categories': 'Kategorien',
        }


class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model = BlogCategory
        fields = ['name']
        labels = {
            'name': 'Kategorie Name',
        }
        help_texts = {
            'name': 'Geben Sie den Namen der Kategorie ein.',
        }