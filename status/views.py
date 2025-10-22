from django.shortcuts import render, get_object_or_404
from .models import App, AppIssue, GlobalIssue, AppStatus
import requests
import time
import socket
import ssl
from django.utils.translation import gettext as _
from urllib.parse import urlparse

# 🔹 Erweiterte Server-Überprüfung
def detailed_speedtest(url):
    """
    Führt eine ausführliche Überprüfung der angegebenen URL durch.
    Gibt ein Dictionary mit leicht verständlichen Ergebnissen zurück.
    """
    result = {
        "url": url,
        "status": _("Offline"),
        "response_time": None,
        "http_code": None,
        "redirects": [],
        "ssl_valid": None,
        "headers": {},
        "error": None,
        "score": 0,  # Gesamtnote (0–100)
        "explanations": []
    }

    # Schema ergänzen, falls nicht angegeben
    if not urlparse(url).scheme:
        url = "http://" + url

    parsed = urlparse(url)

    try:
        # --- 1️⃣ Erreichbarkeit prüfen ---
        start = time.time()
        response = requests.get(url, timeout=6, allow_redirects=True)
        duration = int((time.time() - start) * 1000)

        result["response_time"] = duration
        result["http_code"] = response.status_code
        result["headers"] = dict(response.headers)
        result["redirects"] = [r.url for r in response.history]
        result["final_url"] = response.url
        result["status"] = _("Online") if response.status_code == 200 else _("Erreichbar, aber ungewöhnlicher Statuscode")

        # Bewertung Responsezeit
        if duration < 800:
            result["score"] += 40
            result["explanations"].append(_("Die Antwortzeit ist sehr gut (unter 800 ms)."))
        elif duration < 1500:
            result["score"] += 25
            result["explanations"].append(_("Die Antwortzeit ist in Ordnung, könnte aber optimiert werden."))
        else:
            result["score"] += 10
            result["explanations"].append(_("Die Antwortzeit ist recht hoch – die Seite reagiert langsam."))

        # Bewertung HTTP-Code
        if response.status_code == 200:
            result["score"] += 20
        elif 300 <= response.status_code < 400:
            result["score"] += 10
            result["explanations"].append(_("Die Seite leitet weiter – das ist meist unproblematisch."))
        elif 400 <= response.status_code < 500:
            result["explanations"].append(_("Client-Fehler – die Seite ist eventuell falsch konfiguriert."))
        elif 500 <= response.status_code < 600:
            result["explanations"].append(_("Serverfehler – der Webserver hat ein Problem."))

        # --- 2️⃣ SSL prüfen (nur wenn HTTPS) ---
        if parsed.scheme == "https":
            try:
                context = ssl.create_default_context()
                with socket.create_connection((parsed.hostname, 443), timeout=4) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                        cert = ssock.getpeercert()
                        result["ssl_valid"] = True
                        result["score"] += 20
                        result["explanations"].append(_("Die SSL-Verschlüsselung ist gültig."))
            except Exception:
                result["ssl_valid"] = False
                result["explanations"].append(_("SSL-Fehler – das Zertifikat ist ungültig oder abgelaufen."))

        # --- 3️⃣ Mobile Freundlichkeit (vereinfachter Header-Test) ---
        mobile_test = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"},
            timeout=5
        )
        if "viewport" in mobile_test.text:
            result["score"] += 10
            result["explanations"].append(_("Die Seite ist mobilfreundlich."))
        else:
            result["explanations"].append(_("Die Seite scheint nicht vollständig für Mobilgeräte optimiert zu sein."))

    except requests.exceptions.Timeout:
        result["error"] = _("Timeout – der Server reagierte nicht rechtzeitig.")
    except requests.exceptions.SSLError:
        result["error"] = _("SSL-Fehler – ungültiges oder abgelaufenes Zertifikat.")
    except Exception as e:
        result["error"] = _("Fehler beim Zugriff: ") + str(e)

    return result


def speedtest_form(request):
    return render(request, "status/speedtest_form.html")


def speedtest_result(request):
    url = request.GET.get("url", "").strip()
    if not url:
        return render(request, "status/speedtest_result.html", {"error": _("Bitte gib eine URL ein.")})

    result = detailed_speedtest(url)
    return render(request, "status/speedtest_result.html", {"result": result})

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
