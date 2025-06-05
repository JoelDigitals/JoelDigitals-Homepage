from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField

LANGUAGE_CHOICES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('fr', 'Français'),
]

class Wiki(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    app_name = models.CharField(max_length=100)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    is_developer_only = models.BooleanField(default=False)
    content = RichTextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wiki_articles')
    date = models.DateField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.language})"