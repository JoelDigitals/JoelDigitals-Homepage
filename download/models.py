from django.db import models

class App(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='app_logos/', blank=True, null=True)

    def __str__(self):
        return self.name


class OperatingSystem(models.Model):
    name = models.CharField(max_length=50)  # z.B. Windows, macOS, Linux, Android, iOS

    def __str__(self):
        return self.name


class Download(models.Model):
    app = models.ForeignKey(App, related_name='downloads', on_delete=models.CASCADE)
    operating_system = models.ForeignKey(OperatingSystem, on_delete=models.CASCADE)
    version = models.CharField(max_length=50, blank=True)  # optional Versionsangabe
    file_url = models.FileField(upload_to='downloads/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True, help_text="Externer Download-Link (hat Vorrang vor Datei-Upload)")
    release_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.app.name} - {self.operating_system.name} ({self.version})"

    @property
    def download_url(self):
        return self.external_link or (self.file_url.url if self.file_url else None)
