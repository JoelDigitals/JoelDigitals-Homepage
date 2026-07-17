"""Push-Benachrichtigungen fuer die Joel Digitals App.

Versand laeuft komplett ueber OneSignal (median.co OneSignal-Plugin, App-ID
bereits konfiguriert und im median.co-Build ausgerollt). Das native Plugin
abonniert das Geraet automatisch, sobald die App geoeffnet und die
Benachrichtigungs-Berechtigung erteilt wird. base_app.html liest die daraus
entstehende OneSignal-Player-ID bei jedem Seitenaufruf ueber die
median.onesignal.onesignalInfo()-Bridge aus und speichert sie auf
UserProfile.onesignal_player_id (siehe jd_save_onesignal_player_id_app() in
views.py) - darueber koennen wir gezielt an einzelne Nutzer senden.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ONESIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"


def send_push_notification(title, message, user_ids=None, url=None, data=None):
    """Sendet eine Push-Benachrichtigung per OneSignal.

    `user_ids` sind Django-User-IDs; wir loesen sie ueber
    UserProfile.onesignal_player_id in OneSignal-Player-IDs auf. Nutzer ohne
    gespeicherte Player-ID (z.B. Pushes nie erlaubt) werden dabei
    uebersprungen. Ohne user_ids geht die Nachricht an alle abonnierten
    Geraete (Segment "Subscribed Users").
    """
    app_id = getattr(settings, "ONESIGNAL_APP_ID", "")
    api_key = getattr(settings, "ONESIGNAL_REST_API_KEY", "")

    if not app_id or not api_key:
        logger.info("OneSignal nicht konfiguriert - Push uebersprungen %r: %r", title, message)
        return None

    payload = {
        "app_id": app_id,
        "headings": {"en": title, "de": title},
        "contents": {"en": message, "de": message},
    }

    if user_ids:
        from main.models import UserProfile

        player_ids = list(
            UserProfile.objects.filter(user_id__in=user_ids)
            .exclude(onesignal_player_id="")
            .exclude(onesignal_player_id__isnull=True)
            .values_list("onesignal_player_id", flat=True)
        )
        if not player_ids:
            logger.info("Keine OneSignal-Player-IDs gefunden fuer Push %r (user_ids=%s)", title, user_ids)
            return None
        payload["include_player_ids"] = player_ids
    else:
        payload["included_segments"] = ["Subscribed Users"]

    if url:
        payload["url"] = url
    if data:
        payload["data"] = {str(k): str(v) for k, v in data.items()}

    try:
        response = requests.post(
            ONESIGNAL_API_URL,
            json=payload,
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=10,
        )
        result = response.json()
        if response.status_code >= 300 or result.get("errors"):
            logger.error("OneSignal Push fehlgeschlagen (%s): %s", response.status_code, result)
        else:
            logger.info(
                "OneSignal Push gesendet %r: recipients=%s id=%s",
                title, result.get("recipients"), result.get("id"),
            )
        return result
    except requests.RequestException:
        logger.exception("OneSignal Push fehlgeschlagen")
        return None


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
