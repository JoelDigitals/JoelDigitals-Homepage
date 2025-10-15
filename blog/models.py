from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    teaser_image = models.ImageField(upload_to='blog_teasers/')
    content = RichTextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    categories = models.ManyToManyField(BlogCategory, related_name='posts', blank=True)
    views = models.PositiveIntegerField(default=0)  # 👈 Aufrufe zählen

    def __str__(self):
        return self.title

    def teaser_text(self):
        return self.content[:300] + "..."


class Comment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
