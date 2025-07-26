from django.db import models
from django.utils import timezone

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

class AppIssue(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='issues')
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.app.name} Issue: {self.title}"

class GlobalIssue(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Global Issue: {self.title}"
