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


class DownloadPackage(models.Model):
    """Haupt-App / Paid Download-Paket"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DownloadPackageApp(models.Model):
    """Verknupft eine App mit einem Download-Paket"""
    package = models.ForeignKey(DownloadPackage, on_delete=models.CASCADE, related_name='package_apps')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    os = models.ForeignKey(OperatingSystem, on_delete=models.CASCADE)
    download_link = models.URLField(max_length=500, blank=True, verbose_name="Download-Link",
        help_text="Direkter Link zum Download (hat Vorrang vor Download-Objekt)")
    download = models.ForeignKey(Download, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def get_link(self):
        return self.download_link or (self.download.download_url if self.download else None)

    def __str__(self):
        return f"{self.package.name} – {self.app.name} ({self.os.name})"


class AccessCode(models.Model):
    """Zugangscode fur ein Download-Paket, max. 200 Verwendungen"""
    code = models.CharField(max_length=50, unique=True)
    package = models.ForeignKey(DownloadPackage, on_delete=models.CASCADE, related_name='codes')
    max_uses = models.PositiveIntegerField(default=200)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"{self.code} – {self.package.name} ({self.used_count}/{self.max_uses})"


class CodeRedemption(models.Model):
    """Code-Einlosung durch einen Benutzer"""
    code = models.ForeignKey(AccessCode, on_delete=models.CASCADE, related_name='redemptions')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_info = models.TextField(blank=True)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code.code} – {self.ip_address} – {self.redeemed_at:%d.%m.%Y %H:%M}"


class DownloadSession(models.Model):
    """Tracking eines Downloads"""
    redemption = models.ForeignKey(CodeRedemption, on_delete=models.CASCADE, related_name='downloads')
    package_app = models.ForeignKey(DownloadPackageApp, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DL {self.package_app.app.name} – {self.ip_address}"


class AccessSuspension(models.Model):
    """Sperrung eines Zugangs bei Missbrauch"""
    ip_address = models.GenericIPAddressField()
    reason = models.TextField()
    suspended_at = models.DateTimeField(auto_now_add=True)
    lifted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"SUSPENDED {self.ip_address} – {self.reason[:50]}"
