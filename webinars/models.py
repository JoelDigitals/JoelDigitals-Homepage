from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class Webinar(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titel")
    title_en = models.CharField(max_length=255, blank=True, null=True, verbose_name="Titel (Englisch)")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Beschreibung")
    description_en = models.TextField(blank=True, null=True, verbose_name="Beschreibung (Englisch)")
    image = models.ImageField(upload_to='webinar_images/', null=True, blank=True)
    date_time = models.DateTimeField(verbose_name="Datum & Uhrzeit")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Dauer (Minuten)")
    max_participants = models.PositiveIntegerField(default=50, verbose_name="Max. Teilnehmer")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    recording_url = models.URLField(blank=True, verbose_name="Aufzeichnung (URL)")
    meeting_url = models.URLField(blank=True, verbose_name="Meeting-Link (z.B. Zoom/Teams)")
    registration_start = models.DateTimeField(null=True, blank=True, verbose_name="Anmeldestart")
    registration_end = models.DateTimeField(null=True, blank=True, verbose_name="Anmeldeschluss")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Webinar"
        verbose_name_plural = "Webinare"
        ordering = ['-date_time']

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.date_time > timezone.now()

    @property
    def is_past(self):
        return self.date_time <= timezone.now()

    @property
    def is_registration_open(self):
        now = timezone.now()
        if self.is_past:
            return False
        if self.registration_start and now < self.registration_start:
            return False
        if self.registration_end and now > self.registration_end:
            return False
        return True

    @property
    def registration_opens_soon(self):
        if self.registration_start and self.registration_start > timezone.now():
            return self.registration_start
        return None

    @property
    def spots_remaining(self):
        taken = self.registrations.filter(status='registered').count()
        return max(0, self.max_participants - taken)

    @property
    def is_full(self):
        return self.spots_remaining <= 0


class WebinarRegistration(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registriert'),
        ('cancelled', 'Storniert'),
        ('attended', 'Teilgenommen'),
        ('no_show', 'Nicht erschienen'),
    ]

    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webinar_registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Webinar-Anmeldung"
        verbose_name_plural = "Webinar-Anmeldungen"
        unique_together = ('webinar', 'user')

    def __str__(self):
        return f"{self.user} → {self.webinar.title} ({self.get_status_display()})"
