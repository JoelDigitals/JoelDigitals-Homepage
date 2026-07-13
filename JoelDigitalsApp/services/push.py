import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_push_notification(title, message, user_ids=None, url=None, data=None):
    """Send a push notification via OneSignal.

    Until ONESIGNAL_APP_ID / ONESIGNAL_REST_API_KEY are configured (median.co
    account not set up yet), this only logs the notification instead of
    raising - so order/ticket flows keep working without push credentials.

    `user_ids` are OneSignal "external user ids"; the app should call
    OneSignal.login(str(user.id)) client-side (via the median.co push
    integration) so these ids match.
    """
    app_id = getattr(settings, "ONESIGNAL_APP_ID", "")
    api_key = getattr(settings, "ONESIGNAL_REST_API_KEY", "")

    if not app_id or not api_key:
        logger.info("OneSignal not configured - skipping push %r: %r", title, message)
        return None

    payload = {
        "app_id": app_id,
        "headings": {"en": title, "de": title},
        "contents": {"en": message, "de": message},
    }
    if user_ids:
        payload["include_external_user_ids"] = [str(uid) for uid in user_ids]
    else:
        payload["included_segments"] = ["Subscribed Users"]
    if url:
        payload["url"] = url
    if data:
        payload["data"] = data

    try:
        response = requests.post(
            "https://onesignal.com/api/v1/notifications",
            json=payload,
            headers={
                # os_v2_app_... REST API keys use the "Key" auth scheme (the
                # older legacy REST API keys used "Basic" instead).
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.exception("Failed to send OneSignal push notification")
        return None
