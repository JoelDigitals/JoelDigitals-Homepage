from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import App, AppIssue, GlobalIssue, AppStatus
import requests
import time
import socket
import ssl
from django.utils.translation import gettext as _
from urllib.parse import urlparse
from django.utils import timezone

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


from django.shortcuts import render
from django.utils.translation import gettext as _
from django.contrib import messages
from .utils import comprehensive_website_test, send_test_results_email


def speedtest_form(request):
    """Display the website test form"""
    return render(request, "status/speedtest_form.html")


def speedtest_result(request):
    """Process website test and display results"""
    url = request.GET.get("url", "").strip()
    
    if not url:
        return render(request, "status/speedtest_form.html", {
            "error": _("Bitte gib eine gültige URL ein.")
        })
    
    # Run comprehensive test
    result = comprehensive_website_test(url)
    
    # Handle email sending if requested
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            if send_test_results_email(email, result):
                messages.success(request, _("Ergebnisse wurden erfolgreich per E-Mail versendet!"))
            else:
                messages.error(request, _("Fehler beim E-Mail-Versand. Bitte versuche es später erneut."))
    
    return render(request, "status/speedtest_result.html", {
        "result": result
    })

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

def status_overview(request):
    apps = App.objects.filter(is_active=True)
    global_issues = GlobalIssue.objects.filter(is_resolved=False)

    has_global_issues = global_issues.exists()

    app_data = []
    for app in apps:
        latest = app.statuses.order_by('-timestamp').first()
        has_issues = app.issues.filter(is_resolved=False).exists()

        if has_issues:
            display_status = "issue"
        elif latest and latest.status == "offline":
            display_status = "offline"
        else:
            display_status = "online"

        app_data.append({
            'app': app,
            'status': display_status,
            'latest': latest,
        })

    return render(request, 'status/status_overview.html', {
        'app_data': app_data,
        'global_issues': global_issues,
        'has_global_issues': has_global_issues,
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


@csrf_exempt
def check_all_statuses(request):
    secret = getattr(settings, 'CRON_SECRET', None)
    if secret:
        token = request.GET.get('token', '')
        if token != secret:
            return HttpResponse("Unauthorized", status=401)

    apps = App.objects.filter(is_active=True)
    results = []
    for app in apps:
        try:
            start = time.time()
            response = requests.get(app.server_url, timeout=10)
            duration = int((time.time() - start) * 1000)
            status = "online" if response.status_code == 200 else "offline"
        except Exception:
            status = "offline"
            duration = None

        AppStatus.objects.create(
            app=app,
            status=status,
            response_time_ms=duration,
            message="Cron-Prüfung",
        )
        results.append({"app": app.name, "status": status})

    return JsonResponse({"checked": len(results), "results": results})


# ─── Status Hotline (TwiML / Voice) ──────────────────────────────────────────

@csrf_exempt
def status_hotline(request):
    """
    Gibt TwiML (Voice XML) für eine Telefon-Hotline zurück.
    Liest den aktuellen Status aller Apps und bekannte Probleme vor.
    """
    apps = App.objects.filter(is_active=True)
    global_issues = GlobalIssue.objects.filter(is_resolved=False)
    now = timezone.now()

    lines = ["Willkommen bei der Joel Digitals Status Hotline."]
    lines.append(f"Heute ist der {now.strftime('%d. %B %Y')}, es ist {now.strftime('%H:%M')} Uhr.")

    # Global issues
    if global_issues.exists():
        lines.append("Achtung, es liegen globale Störungen vor.")
        for issue in global_issues:
            lines.append(f"{issue.title}. {issue.description}")
    else:
        lines.append("Es liegen keine globalen Störungen vor.")

    # App status
    online_count = 0
    offline_count = 0
    issue_count = 0
    status_details = []

    for app in apps:
        latest = app.statuses.order_by('-timestamp').first()
        has_issues = app.issues.filter(is_resolved=False).exists()

        if has_issues:
            status_details.append(f"{app.name} hat bekannte Probleme.")
            for issue in app.issues.filter(is_resolved=False):
                status_details.append(f"{issue.title}. {issue.description}")
            issue_count += 1
        elif latest and latest.status == "offline":
            status_details.append(f"{app.name} ist offline.")
            offline_count += 1
        else:
            status_details.append(f"{app.name} ist online.")
            online_count += 1

    lines.append(f"Von {len(apps)} überwachten Diensten sind {online_count} online, {offline_count} offline und {issue_count} haben bekannte Probleme.")

    if status_details:
        lines.append("Im Einzelnen:")
        lines.extend(status_details)

    lines.append("Vielen Dank für Ihren Anruf. Bei Fragen erreichen Sie uns auch per E-Mail unter info@joel-digitals.de.")

    text = ". ".join(lines)

    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="female" language="de-DE">{text}</Say>
</Response>'''

    return HttpResponse(twiml, content_type="text/xml")


# ─── Free Tools ────────────────────────────────────────────────────────────────

def tools_overview(request):
    return render(request, "status/tools_overview.html")


def tool_ssl_check(request):
    target = request.GET.get("target", "").strip()
    result = None
    error = None

    if target:
        import ssl, socket
        hostname = target.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issued_to = dict(cert.get("subject", []))
                    issued_by = dict(cert.get("issuer", []))
                    not_before = cert.get("notBefore", "")
                    not_after = cert.get("notAfter", "")
                    from datetime import datetime
                    expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    remaining = (expires - datetime.now()).days

                    result = [
                        ("Domain", hostname),
                        ("Ausgestellt für", issued_to.get("commonName", "N/A")),
                        ("Ausgestellt von", issued_by.get("commonName", "N/A")),
                        ("Gültig von", not_before),
                        ("Gültig bis", not_after),
                        ("Tage verbleibend", f'{remaining} Tage' if remaining > 0 else '<span style="color:#ef4444">ABGELAUFEN</span>'),
                        ("SSL Version", ssock.version()),
                        ("Cipher", ssock.cipher()[0]),
                    ]
        except Exception as e:
            error = f"SSL-Fehler: {e}"

    return render(request, "status/tool_result.html", {
        "tool_title": "SSL Checker",
        "tool_subtitle": "Prüfe SSL-Zertifikate auf Gültigkeit und Sicherheit",
        "header_icon": "fas fa-lock",
        "gradient_from": "#4facfe",
        "gradient_to": "#00f2fe",
        "input_placeholder": "z.B. joel-digitals.de",
        "button_text": "SSL prüfen",
        "result_icon": "fas fa-shield-alt",
        "result_title": "Zertifikatsdetails",
        "result": result,
        "error": error,
    })


def tool_dns_lookup(request):
    target = request.GET.get("target", "").strip()
    records = None
    error = None

    if target:
        import socket
        hostname = target.replace("https://", "").replace("http://", "").split("/")[0]
        try:
            ips = socket.getaddrinfo(hostname, 80)
            seen = set()
            records = []
            for ip in ips:
                addr = ip[4][0]
                if addr not in seen:
                    seen.add(addr)
                    records.append(f"A  {addr}")
        except Exception as e:
            error = f"DNS-Fehler: {e}"

    return render(request, "status/tool_result.html", {
        "tool_title": "DNS Lookup",
        "tool_subtitle": "Ermittle IP-Adressen und DNS-Einträge",
        "header_icon": "fas fa-globe",
        "gradient_from": "#43e97b",
        "gradient_to": "#38f9d7",
        "input_placeholder": "z.B. joel-digitals.de",
        "button_text": "DNS abfragen",
        "result_icon": "fas fa-network-wired",
        "result_title": "IP-Adressen (A-Records)",
        "records": records,
        "error": error,
    })


def tool_ping(request):
    target = request.GET.get("target", "").strip()
    result = None
    error = None

    if target:
        import requests
        url = target if target.startswith("http") else f"https://{target}"
        try:
            start = time.time()
            r = requests.get(url, timeout=10, allow_redirects=True)
            duration = int((time.time() - start) * 1000)
            result = [
                ("URL", url),
                ("Status", f'{r.status_code} {"✅" if r.status_code == 200 else "⚠️"}'),
                ("Antwortzeit", f"{duration} ms"),
                ("Weiterleitungen", str(len(r.history))),
                ("Server", r.headers.get("Server", "N/A")),
                ("Content-Type", r.headers.get("Content-Type", "N/A")),
            ]
        except Exception as e:
            error = f"Fehler: {e}"

    return render(request, "status/tool_result.html", {
        "tool_title": "Ping Test",
        "tool_subtitle": "Prüfe Erreichbarkeit und Antwortzeit eines Servers",
        "header_icon": "fas fa-signal",
        "gradient_from": "#fa709a",
        "gradient_to": "#fee140",
        "input_placeholder": "z.B. https://joel-digitals.de",
        "button_text": "Pingen",
        "result_icon": "fas fa-tachometer-alt",
        "result_title": "Antwortdetails",
        "result": result,
        "error": error,
    })


def tool_http_headers(request):
    target = request.GET.get("target", "").strip()
    result = None
    error = None

    if target:
        import requests
        url = target if target.startswith("http") else f"https://{target}"
        try:
            r = requests.get(url, timeout=10, allow_redirects=True)
            security_checks = {
                "Strict-Transport-Security": ("HSTS", "Schützt vor SSL-Stripping"),
                "Content-Security-Policy": ("CSP", "Schützt vor XSS"),
                "X-Content-Type-Options": ("XCTO", "Verhindert MIME-Sniffing"),
                "X-Frame-Options": ("XFO", "Schützt vor Clickjacking"),
                "X-XSS-Protection": ("XXSS", "XSS-Filter (veraltet)"),
                "Referrer-Policy": ("Referrer", "Kontrolliert Referrer-Header"),
                "Permissions-Policy": ("Permissions", "Kontrolliert Browser-APIs"),
            }
            rows = []
            for h, (short, desc) in security_checks.items():
                val = r.headers.get(h, None)
                if val:
                    rows.append((short, f'<span class="status-badge valid">✅ {val[:50]}</span>'))
                else:
                    rows.append((short, '<span class="status-badge invalid">❌ Fehlt</span>'))

            result = [
                ("HTTP Status", str(r.status_code)),
                ("URL", url),
                ("Server", r.headers.get("Server", "N/A")),
            ] + rows + [
                ("Weitere Header", f'{len(r.headers)} gesamt'),
            ]
        except Exception as e:
            error = f"Fehler: {e}"

    return render(request, "status/tool_result.html", {
        "tool_title": "HTTP Headers",
        "tool_subtitle": "Prüfe HTTP-Response-Header und Sicherheitsheader",
        "header_icon": "fas fa-code",
        "gradient_from": "#a18cd1",
        "gradient_to": "#fbc2eb",
        "input_placeholder": "z.B. https://joel-digitals.de",
        "button_text": "Header prüfen",
        "result_icon": "fas fa-headers",
        "result_title": "Response Header",
        "result": result,
        "error": error,
    })
