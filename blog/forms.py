# blog/forms.py

from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import BlogPost, BlogCategory

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = [
            'title_de', 'title_en', 
            'main_image_url', 'main_image_thumb_url', 'main_image_medium_url', 'main_image_delete_url',
            'teaser_image',
            'content_de', 'content_en',
            'is_published', 'published_at', 'categories'
        ]
        widgets = {
            'main_image_url': forms.URLInput(attrs={'placeholder': 'https://i.ibb.co/...'}),
            'main_image_thumb_url': forms.URLInput(attrs={'placeholder': 'https://i.ibb.co/... (thumbnail)'}),
            'main_image_medium_url': forms.URLInput(attrs={'placeholder': 'https://i.ibb.co/... (medium)'}),
            'main_image_delete_url': forms.URLInput(attrs={'placeholder': 'https://ibb.co/.../delete'}),
            # DATETIME FIELD HIER DEFINIEREN:
            'published_at': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'  # Wichtig für korrektes Parsing
            ),
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