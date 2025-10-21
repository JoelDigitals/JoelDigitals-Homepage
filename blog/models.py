from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title_de = models.CharField(max_length=200, verbose_name="Titel (DE)")
    title_en = models.CharField(max_length=200, verbose_name="Titel (EN)")
    teaser_image = models.ImageField(upload_to='blog_teasers/')
    content_de = RichTextField(verbose_name="Inhalt (DE)")
    content_en = RichTextField(verbose_name="Inhalt (EN)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    categories = models.ManyToManyField(BlogCategory, related_name='posts', blank=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title_de  # oder dynamisch nach Sprache

    def teaser_text(self, lang='de'):
        if lang == 'en':
            return self.content_en[:300] + "..."
        return self.content_de[:300] + "..."



class Comment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
