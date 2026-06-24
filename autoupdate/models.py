from django.db import models


class AutoUpdateApp(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Auto-Update App"
        verbose_name_plural = "Auto-Update Apps"

    def __str__(self):
        return self.name


class AutoUpdateVersion(models.Model):
    app = models.ForeignKey(
        AutoUpdateApp, on_delete=models.CASCADE,
        related_name='versions'
    )
    version = models.CharField(max_length=50, help_text="Format: 1.0.0.0")
    release_date = models.DateField()
    download_link = models.URLField(max_length=500)
    release_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Version"
        verbose_name_plural = "Versionen"
        ordering = ['-release_date']
        unique_together = ['app', 'version']

    def __str__(self):
        return f"{self.app.name} v{self.version}"
