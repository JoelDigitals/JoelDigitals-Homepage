"""Push-Benachrichtigungen fuer die Joel Digitals App.

Nutzt Firebase Cloud Messaging (FCM) - dasselbe Muster wie im JDS-Management-
Projekt (main.Device / send_push_to_user): der Client registriert beim Login
(oder ueber /api/register-device/) sein firebase_token, wir schicken darueber.
median.co unterstuetzt FCM nativ ueber die "median.firebase" JS-Bridge (siehe
base_app.html), dieselbe Bruecke, die JDS Management fuer ihre median-App nutzt.

Die OneSignal-Integration (Zugangsdaten-Check, median.co-Plugin) bleibt
bestehen, wird aber nicht mehr fuers eigentliche Versenden benutzt.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None
_firebase_init_failed = False


def _get_firebase_app():
    """Initialisiert die Firebase Admin SDK lazy und einmalig.

    Erwartet FIREBASE_SERVICE_ACCOUNT_JSON als Umgebungsvariable mit dem
    kompletten Inhalt der Service-Account-JSON-Datei (aus der Firebase
    Console -> Projekteinstellungen -> Dienstkonten -> Neuen privaten
    Schluessel generieren). Ohne diese Variable bleibt Push deaktiviert
    (loggt nur), statt die Seite crashen zu lassen.
    """
    global _firebase_app, _firebase_init_failed
    if _firebase_app is not None or _firebase_init_failed:
        return _firebase_app

    raw = getattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        _firebase_init_failed = True
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_dict = json.loads(raw)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app
    except Exception:
        logger.exception("Firebase Admin SDK Initialisierung fehlgeschlagen")
        _firebase_init_failed = True
        return None


def send_push_notification(title, message, user_ids=None, url=None, data=None):
    """Sendet eine Push-Benachrichtigung per Firebase Cloud Messaging.

    `user_ids` sind Django-User-IDs (JoelDigitalsApp.models.Device.user_id).
    Ohne user_ids geht die Nachricht an ALLE registrierten Geraete.
    Ungueltige Tokens (App deinstalliert, Token abgelaufen) werden nach dem
    Versand automatisch aus der DB entfernt - gleiches Verhalten wie
    send_push_to_user() im JDS-Management-Projekt.
    """
    app = _get_firebase_app()
    if not app:
        logger.info("Firebase nicht konfiguriert - Push uebersprungen %r: %r", title, message)
        return None

    from ..models import Device

    tokens_qs = Device.objects.exclude(firebase_token="")
    if user_ids:
        tokens_qs = tokens_qs.filter(user_id__in=user_ids)
    tokens = list(tokens_qs.values_list("firebase_token", flat=True))

    if not tokens:
        logger.info("Keine Firebase-Tokens gefunden fuer Push %r (user_ids=%s)", title, user_ids)
        return None

    from firebase_admin import messaging

    try:
        fcm_message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=message),
            data={str(k): str(v) for k, v in (data or {}).items()},
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(link=url) if url else None,
            ) if url else None,
            tokens=tokens,
        )
        response = messaging.send_multicast(fcm_message, app=app)
        logger.info("Firebase Push gesendet: %s/%s erfolgreich", response.success_count, len(tokens))

        if response.failure_count:
            invalid_tokens = [
                tokens[i] for i, r in enumerate(response.responses) if not r.success
            ]
            if invalid_tokens:
                Device.objects.filter(firebase_token__in=invalid_tokens).delete()
                logger.info("Entfernt %s ungueltige Firebase-Tokens", len(invalid_tokens))

        return response
    except Exception:
        logger.exception("Firebase Push fehlgeschlagen")
        return None


def register_device(user, firebase_token, device_type="", app_version=""):
    """Legt ein Device an/aktualisiert es - gleiche Logik wie register_device()
    und custom_login() im JDS-Management-Projekt."""
    from ..models import Device

    if not firebase_token or len(firebase_token) < 20:
        return None

    device, created = Device.objects.update_or_create(
        firebase_token=firebase_token,
        defaults={
            "user": user if user and user.is_authenticated else None,
            "device_type": device_type,
            "app_version": app_version,
        },
    )
    return device


# ─────────────────────────────────────────────────────────────────────────
# OneSignal (median.co-Plugin bleibt konfiguriert, wird aber nicht mehr fuers
# Versenden benutzt - nur noch fuer den 10-Tage-Zugangsdaten-Check).
# ─────────────────────────────────────────────────────────────────────────

def check_onesignal_credentials():
    """Prueft, ob ONESIGNAL_APP_ID/ONESIGNAL_REST_API_KEY noch gueltig sind
    (z.B. falls der Key mal in OneSignal rotiert/geloescht wird), ohne dabei
    eine echte Push-Benachrichtigung zu versenden. Wird vom Cron-Endpunkt
    alle 10 Tage aufgerufen (siehe JoelDigitalsApp/cron.py).

    Gibt (success: bool, detail: str) zurueck.
    """
    app_id = getattr(settings, "ONESIGNAL_APP_ID", "")
    api_key = getattr(settings, "ONESIGNAL_REST_API_KEY", "")

    if not app_id or not api_key:
        return False, "ONESIGNAL_APP_ID/ONESIGNAL_REST_API_KEY nicht konfiguriert."

    try:
        response = requests.get(
            f"https://onesignal.com/api/v1/apps/{app_id}",
            headers={"Authorization": f"Key {api_key}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "OK"
        return False, f"OneSignal API antwortete mit Status {response.status_code}: {response.text[:200]}"
    except requests.RequestException as e:
        logger.exception("OneSignal Zugangsdaten-Check fehlgeschlagen")
        return False, str(e)[:200]
