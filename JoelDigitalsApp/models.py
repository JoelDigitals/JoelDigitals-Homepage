from django.conf import settings
from django.db import models


class CallbackRequest(models.Model):
    """Rückrufwunsch zu einer Bestellung. Bewusst KEIN SupportTicket - das
    landet nicht in der normalen Ticket-Warteschlange, sondern nur hier +
    Benachrichtigungs-Mail an den Support."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='callback_requests')
    order = models.ForeignKey('shop_ourapps.Order', on_delete=models.CASCADE, related_name='callback_requests')
    phone = models.CharField(max_length=50, blank=True, help_text="Leer = Nummer aus der Bestellung verwenden")
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rückruf für Bestellung #{self.order_id} von {self.user}"


class PushHealthCheck(models.Model):
    """Protokoll der periodischen OneSignal-Zugangsdaten-Pruefung (alle 10 Tage,
    ausgeloest vom Cron-Endpunkt /api/push-check/). Damit sieht man im Admin
    sofort, falls die App-ID/REST-Key mal ungueltig werden (z.B. Key rotiert)."""
    checked_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f"OneSignal-Check {self.checked_at:%Y-%m-%d %H:%M} - {'OK' if self.success else 'FEHLER'}"


class Device(models.Model):
    """Ein Firebase-Cloud-Messaging-Geraet (Push-Token). Gleiches Muster wie
    main.Device im JDS-Management-Projekt: firebase_token wird beim Login
    (oder per /api/register-device/) registriert; send_push_notification()
    schickt an alle Tokens eines Users und entfernt ungueltige Tokens
    automatisch."""
    DEVICE_TYPES = (
        ("ios", "iOS"),
        ("android", "Android"),
        ("web", "Web"),
    )

    firebase_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="jd_devices",
    )
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_type or 'unknown'} - {self.user} ({self.firebase_token[:16]}…)"
