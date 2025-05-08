# blog/forms.py

from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import BlogPost, BlogCategory


class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(), label="Inhalt")

    class Meta:
        model = BlogPost
        fields = ['title', 'teaser_image', 'content', 'is_published', 'categories']
        labels = {
            'title': 'Titel',
            'teaser_image': 'Teaser-Bild',
            'is_published': 'Veröffentlicht?',
            'categories': 'Kategorien',
        }
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            'title': 'Geben Sie den Titel des Blogbeitrags ein.',
            'teaser_image': 'Wählen Sie ein Bild für die Vorschau aus.',
            'is_published': 'Aktivieren Sie dieses Feld, um den Beitrag zu veröffentlichen.',
            'categories': 'Wählen Sie eine oder mehrere Kategorien aus.',
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