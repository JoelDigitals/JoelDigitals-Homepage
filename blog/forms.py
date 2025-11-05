# blog/forms.py

from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import BlogPost, BlogCategory


class BlogPostForm(forms.ModelForm):
    published_at = forms.DateTimeField(
        label="Veröffentlichungsdatum",
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
        })
    )
    content_de = forms.CharField(widget=CKEditorWidget(), label="Inhalt (DE)")
    content_en = forms.CharField(widget=CKEditorWidget(), label="Inhalt (EN)")

    class Meta:
        model = BlogPost
        fields = ['title_de', 'title_en', 'teaser_image', 'content_de', 'content_en', 'is_published', 'published_at', 'categories']



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