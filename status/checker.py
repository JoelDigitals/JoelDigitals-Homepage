import time
import requests
from status.models import App, AppStatus


def check_single_app(app):
    try:
        start = time.time()
        response = requests.get(app.server_url, timeout=10)
        duration = int((time.time() - start) * 1000)
        if response.status_code == 200:
            return "online", duration
        return "offline", None
    except Exception:
        return "offline", None


def check_all_apps():
    apps = App.objects.filter(is_active=True)
    results = []
    for app in apps:
        status, duration = check_single_app(app)
        AppStatus.objects.create(
            app=app,
            status=status,
            response_time_ms=duration,
            message="Automatische Prüfung",
        )
        results.append((app.name, status))
    return results
