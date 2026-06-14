from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title_de = models.CharField(max_length=200, verbose_name="Titel (DE)")
    title_en = models.CharField(max_length=200, verbose_name="Titel (EN)")
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug")
    teaser_image = models.ImageField(upload_to='blog_teasers/', blank=True, null=True)
    content_de = RichTextField(verbose_name="Inhalt (DE)")
    content_en = RichTextField(verbose_name="Inhalt (EN)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    categories = models.ManyToManyField(BlogCategory, related_name='posts', blank=True)
    views = models.PositiveIntegerField(default=0)

    main_image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="ImgBB Bild URL")
    main_image_thumb_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="ImgBB Thumbnail URL")
    main_image_medium_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="ImgBB Medium URL")
    main_image_delete_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="ImgBB Lösch-URL")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title_de
            slug = slugify(base)
            if not slug:
                slug = f"post-{BlogPost.objects.count() + 1}"
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slugify(base)}-{BlogPost.objects.count() + 1}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_de

    def teaser_text(self, lang='de'):
        if lang == 'en':
            return self.content_en[:300] + "..."
        return self.content_de[:300] + "..."

    def get_main_image_url(self):
        """
        Priorisiert ImgBB URL, fallback auf lokales teaser_image
        """
        if self.main_image_url:
            return self.main_image_url
        elif self.teaser_image:
            return self.teaser_image.url
        return None

    def get_main_image_thumb(self):
        """
        Thumbnail mit Priorisierung
        """
        if self.main_image_thumb_url:
            return self.main_image_thumb_url
        elif self.teaser_image:
            return self.teaser_image.url  # oder thumbnail-Version wenn verfügbar
        return None

class Comment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title_de}"


class BlogViewTracking(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='daily_views')
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('post', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.post.title_de} – {self.date}: {self.count}"
