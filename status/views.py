from django.shortcuts import render, get_object_or_404
from .models import App, AppIssue, GlobalIssue, AppStatus
import requests
import time

def check_server_status(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=3)
        duration = int((time.time() - start) * 1000)
        if response.status_code == 200:
            return "online", duration
        return "offline", None
    except Exception:
        return "offline", None

# ⬇️ Nur globale Probleme + App-Liste ohne Prüfung
def status_overview(request):
    apps = App.objects.filter(is_active=True)
    global_issues = GlobalIssue.objects.filter(is_resolved=False)
    return render(request, 'status/status_overview.html', {
        'apps': apps,
        'global_issues': global_issues
    })

# ⬇️ Hier wird beim Aufruf die App live geprüft
def app_detail(request, app_id):
    app = get_object_or_404(App, pk=app_id)
    current_status, response_time = check_server_status(app.server_url)

    # 📦 Speichere jeden Statusaufruf in AppStatus
    AppStatus.objects.create(
        app=app,
        status=current_status,
        response_time_ms=response_time,
        message="Automatische Prüfung"
    )

    unresolved_issues = app.issues.filter(is_resolved=False)

    return render(request, 'status/app_detail.html', {
        'app': app,
        'status': current_status,
        'response_time': response_time,
        'issues': unresolved_issues
    })
