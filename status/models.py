from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class App(models.Model):
    name = models.CharField(max_length=100)
    server_url = models.URLField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class AppStatus(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='statuses')
    status = models.CharField(max_length=20, choices=[("online", "Online"), ("offline", "Offline")])
    response_time_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.app.name} - {self.status} - {self.timestamp:%Y-%m-%d %H:%M}"


SEVERITY_CHOICES = [
    ("minor", _("Minor")),
    ("major", _("Major")),
    ("critical", _("Critical")),
]

ISSUE_STATUS_CHOICES = [
    ("investigating", _("Investigating")),
    ("identified", _("Identified")),
    ("monitoring", _("Monitoring")),
    ("resolved", _("Resolved")),
]


class AppIssue(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='issues')
    title_de = models.CharField(max_length=200, verbose_name="Titel (DE)")
    title_en = models.CharField(max_length=200, verbose_name="Titel (EN)", blank=True)
    description_de = models.TextField(verbose_name="Beschreibung (DE)")
    description_en = models.TextField(verbose_name="Beschreibung (EN)", blank=True)
    is_resolved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="minor")
    status = models.CharField(max_length=20, choices=ISSUE_STATUS_CHOICES, default="investigating")
    started_at = models.DateTimeField(default=timezone.now, help_text="Wann das Problem tatsächlich begann")
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.app.name} Issue: {self.title_de}"

class GlobalIssue(models.Model):
    title_de = models.CharField(max_length=200, verbose_name="Titel (DE)")
    title_en = models.CharField(max_length=200, verbose_name="Titel (EN)", blank=True)
    description_de = models.TextField(verbose_name="Beschreibung (DE)")
    description_en = models.TextField(verbose_name="Beschreibung (EN)", blank=True)
    is_resolved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="minor")
    status = models.CharField(max_length=20, choices=ISSUE_STATUS_CHOICES, default="investigating")
    started_at = models.DateTimeField(default=timezone.now, help_text="Wann das Problem tatsächlich begann")
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Global Issue: {self.title_de}"
