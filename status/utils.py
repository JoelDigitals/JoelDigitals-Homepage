import time
import socket
import ssl
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from django.utils.translation import gettext as _
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
from datetime import datetime


def comprehensive_website_test(url):
    """
    Kundenakquise-optimierte Analyse: Strengere Bewertung, SEO-lastig, mehr Verbesserungspotenzial zeigen.
    """
    result = {
        "url": url,
        "test_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "overall_score": 0,
        "category_scores": {},
        
        "performance": {
            "response_time": None,
            "page_size": 0,
            "compression": False,
            "score": 0
        },
        
        "seo": {
            "title": None,
            "title_length": 0,
            "meta_description": None,
            "meta_description_length": 0,
            "h1_tags": [],
            "h2_count": 0,
            "images_without_alt": 0,
            "total_images": 0,
            "robots_txt": False,
            "sitemap_xml": False,
            "structured_data": False,
            "open_graph": False,
            "twitter_cards": False,
            "canonical_url": None,
            "score": 0
        },
        
        "security": {
            "ssl_valid": False,
            "ssl_issuer": None,
            "ssl_expires": None,
            "https_redirect": False,
            "security_headers": {},
            "score": 0
        },
        
        "server": {
            "http_code": None,
            "server_type": None,
            "ip_address": None,
            "cdn_detected": False,
            "cache_headers": False,
            "gzip_enabled": False,
            "score": 0
        },
        
        "mobile": {
            "viewport_meta": False,
            "mobile_friendly": False,
            "responsive_images": False,
            "score": 0
        },
        
        "accessibility": {
            "lang_attribute": False,
            "alt_texts": 0,
            "aria_labels": 0,
            "score": 0
        },
        
        "status": _("Offline"),
        "error": None,
        "warnings": [],
        "recommendations": []
    }

    if not urlparse(url).scheme:
        url = "https://" + url
    
    parsed = urlparse(url)
    result["url"] = url

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        start_time = time.time()
        response = requests.get(url, timeout=15, allow_redirects=True, headers=headers)
        total_time = int((time.time() - start_time) * 1000)
        
        result["performance"]["response_time"] = total_time
        result["performance"]["page_size"] = len(response.content)
        result["server"]["http_code"] = response.status_code
        result["status"] = _("Online")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ========== PERFORMANCE (0-100) - Strenger ==========
        perf_score = 20  # Niedriger Basiswert
        
        # Ladezeit (max 40 Punkte, strenger)
        if total_time < 800:
            perf_score += 40
            result["recommendations"].append(_("✓ Hervorragende Ladezeit"))
        elif total_time < 1500:
            perf_score += 25
        elif total_time < 2500:
            perf_score += 10
            result["warnings"].append(_("⚠ Ladezeit verbesserungswürdig (>1.5s)"))
        elif total_time < 4000:
            perf_score -= 10
            result["warnings"].append(_("❌ Langsame Ladezeit beeinträchtigt Conversions"))
        else:
            perf_score -= 25
            result["warnings"].append(_("❌ Kritische Ladezeit - sofort optimieren!"))
        
        # Seitengröße (max 30 Punkte)
        page_size_kb = len(response.content) / 1024
        if page_size_kb < 500:
            perf_score += 30
        elif page_size_kb < 1000:
            perf_score += 20
        elif page_size_kb < 2000:
            perf_score += 10
            result["warnings"].append(_("⚠ Seitengröße reduzieren für bessere Mobile-Performance"))
        else:
            perf_score -= 15
            result["warnings"].append(_("❌ Seite zu groß - Images optimieren nötig"))
        
        # Kompression (max 10 Punkte)
        if 'Content-Encoding' in response.headers and 'gzip' in response.headers['Content-Encoding'].lower():
            result["performance"]["compression"] = True
            result["server"]["gzip_enabled"] = True
            perf_score += 10
        else:
            result["warnings"].append(_("❌ GZIP-Komprimierung fehlt - einfach zu fixen!"))
        
        result["performance"]["score"] = max(0, min(100, perf_score))
        
        # ========== SEO (0-100) - WICHTIGSTE KATEGORIE ==========
        seo_score = 15  # Sehr niedriger Basiswert - SEO muss erarbeitet werden
        
        # Title (max 25 Punkte, kritisch)
        title_tag = soup.find('title')
        if title_tag:
            result["seo"]["title"] = title_tag.get_text().strip()
            result["seo"]["title_length"] = len(result["seo"]["title"])
            
            if 40 <= result["seo"]["title_length"] <= 60:
                seo_score += 25
                result["recommendations"].append(_("✓ Title-Tag optimal für Google"))
            elif 30 <= result["seo"]["title_length"] < 40:
                seo_score += 15
                result["warnings"].append(_("⚠ Title-Tag könnte länger sein (40-60 Zeichen optimal)"))
            elif 10 <= result["seo"]["title_length"] < 30:
                seo_score += 5
                result["warnings"].append(_("❌ Title-Tag zu kurz - verpasst Ranking-Chancen"))
            elif result["seo"]["title_length"] > 60:
                seo_score += 10
                result["warnings"].append(_("⚠ Title-Tag zu lang - wird in SERPs abgeschnitten"))
            else:
                seo_score -= 5
        else:
            seo_score -= 20
            result["warnings"].append(_("❌ KRITISCH: Kein Title-Tag - Google kann Seite nicht einordnen!"))
        
        # Meta Description (max 20 Punkte)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result["seo"]["meta_description"] = meta_desc.get('content').strip()
            result["seo"]["meta_description_length"] = len(result["seo"]["meta_description"])
            
            if 150 <= result["seo"]["meta_description_length"] <= 160:
                seo_score += 20
                result["recommendations"].append(_("✓ Meta-Description optimal für CTR"))
            elif 120 <= result["seo"]["meta_description_length"] < 150:
                seo_score += 15
            elif 50 <= result["seo"]["meta_description_length"] < 120:
                seo_score += 8
                result["warnings"].append(_("⚠ Meta-Description zu kurz für maximale Wirkung"))
            else:
                seo_score += 5
                result["warnings"].append(_("⚠ Meta-Description Länge suboptimal"))
        else:
            result["warnings"].append(_("❌ Keine Meta-Description - verpasste Click-Through-Chance!"))
        
        # H1 Tags (max 20 Punkte, wichtig für SEO)
        h1_tags = soup.find_all('h1')
        result["seo"]["h1_tags"] = [h1.get_text().strip() for h1 in h1_tags]
        
        if len(h1_tags) == 1:
            seo_score += 20
            result["recommendations"].append(_("✓ Perfekte H1-Struktur"))
        elif len(h1_tags) == 0:
            result["warnings"].append(_("❌ Kein H1-Tag - Hauptkeyword fehlt!"))
        else:
            seo_score += 5
            result["warnings"].append(_("⚠ Mehrere H1-Tags verwirren Suchmaschinen"))
        
        # H2-H6 Struktur
        result["seo"]["h2_count"] = len(soup.find_all('h2'))
        if result["seo"]["h2_count"] == 0:
            result["warnings"].append(_("⚠ Keine H2-Überschriften - Inhalt schlecht strukturiert"))
        
        # Bilder & Alt-Texte (max 15 Punkte, wichtig für Image-SEO)
        images = soup.find_all('img')
        result["seo"]["total_images"] = len(images)
        result["seo"]["images_without_alt"] = sum(1 for img in images if not img.get('alt'))
        
        if result["seo"]["total_images"] > 0:
            alt_coverage = (result["seo"]["total_images"] - result["seo"]["images_without_alt"]) / result["seo"]["total_images"]
            if alt_coverage >= 0.95:
                seo_score += 15
                result["recommendations"].append(_("✓ Perfekte Alt-Texte für Image-SEO"))
            elif alt_coverage >= 0.8:
                seo_score += 10
                result["warnings"].append(_("⚠ Einige Bilder ohne Alt-Text - verpasster Traffic"))
            elif alt_coverage >= 0.5:
                seo_score += 5
                result["warnings"].append(_("❌ Viele Bilder ohne Alt-Text - schlecht für Accessibility & SEO"))
            else:
                result["warnings"].append(_("❌ Bilder nicht optimiert - Google kann Inhalt nicht verstehen"))
        
        # Robots.txt (max 10 Punkte)
        try:
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            robots_response = requests.get(robots_url, timeout=5, headers=headers)
            if robots_response.status_code == 200:
                result["seo"]["robots_txt"] = True
                seo_score += 10
            else:
                result["warnings"].append(_("⚠ Robots.txt fehlt - Crawling nicht gesteuert"))
        except:
            result["warnings"].append(_("❌ Robots.txt nicht erreichbar"))
        
        # Sitemap (max 10 Punkte)
        try:
            sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
            sitemap_response = requests.get(sitemap_url, timeout=5, headers=headers)
            if sitemap_response.status_code == 200:
                result["seo"]["sitemap_xml"] = True
                seo_score += 10
                result["recommendations"].append(_("✓ Sitemap vorhanden"))
            else:
                result["warnings"].append(_("⚠ Keine XML-Sitemap - Indexierung erschwert"))
        except:
            result["warnings"].append(_("❌ Sitemap fehlt - Google findet nicht alle Seiten"))
        
        # Strukturierte Daten (max 10 Punkte)
        if soup.find('script', attrs={'type': 'application/ld+json'}):
            result["seo"]["structured_data"] = True
            seo_score += 10
            result["recommendations"].append(_("✓ Rich Snippets möglich"))
        else:
            result["warnings"].append(_("⚠ Keine strukturierten Daten - keine Rich Snippets in Google"))
        
        # Open Graph (max 5 Punkte)
        if soup.find('meta', property='og:title'):
            result["seo"]["open_graph"] = True
            seo_score += 5
        
        # Twitter Cards (max 5 Punkte)
        if soup.find('meta', attrs={'name': 'twitter:card'}):
            result["seo"]["twitter_cards"] = True
            seo_score += 5
        
        # Canonical URL (max 5 Punkte, wichtig für Duplicate Content)
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            result["seo"]["canonical_url"] = canonical.get('href')
            seo_score += 5
        else:
            result["warnings"].append(_("⚠ Canonical Tag fehlt - Duplicate Content Risiko"))
        
        result["seo"]["score"] = max(0, min(100, seo_score))
        
        # ========== SECURITY (0-100) ==========
        security_score = 30
        
        # SSL/HTTPS (max 50 Punkte, kritisch)
        if parsed.scheme == "https":
            try:
                context = ssl.create_default_context()
                with socket.create_connection((parsed.hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                        cert = ssock.getpeercert()
                        result["security"]["ssl_valid"] = True
                        result["security"]["ssl_issuer"] = dict(x[0] for x in cert['issuer'])
                        
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        result["security"]["ssl_expires"] = not_after.strftime("%d.%m.%Y")
                        days_until_expiry = (not_after - datetime.now()).days
                        
                        if days_until_expiry > 60:
                            security_score += 50
                            result["recommendations"].append(_("✓ SSL sicher"))
                        else:
                            security_score += 30
                            result["warnings"].append(_(f"⚠ SSL läuft in {days_until_expiry} Tagen ab"))
            except:
                security_score -= 20
                result["warnings"].append(_("❌ SSL-Zertifikat Problem!"))
        else:
            security_score -= 30
            result["warnings"].append(_("❌ KEIN HTTPS! Google bevorzugt sichere Seiten - Ranking-Nachteil!"))
        
        # Security Headers (max 30 Punkte)
        security_headers = {
            'Strict-Transport-Security': 'HSTS',
            'X-Content-Type-Options': 'Content-Type Protection',
            'X-Frame-Options': 'Clickjacking Protection',
            'X-XSS-Protection': 'XSS Protection',
            'Content-Security-Policy': 'CSP',
            'Referrer-Policy': 'Referrer Policy'
        }
        
        headers_found = 0
        for header, name in security_headers.items():
            if header in response.headers:
                result["security"]["security_headers"][name] = response.headers[header]
                headers_found += 1
        
        security_score += headers_found * 5
        
        if headers_found < 3:
            result["warnings"].append(_("⚠ Wichtige Security-Header fehlen - Angriffsrisiko"))
        
        result["security"]["score"] = max(0, min(100, security_score))
        
        # ========== SERVER (0-100) ==========
        server_score = 30
        
        # CDN (max 30 Punkte)
        cdn_headers = ['CF-RAY', 'X-CDN', 'X-Cache', 'X-Fastly-Request-ID', 'X-Cloud-Trace-Context']
        for header in cdn_headers:
            if header in response.headers:
                result["server"]["cdn_detected"] = True
                server_score += 30
                result["recommendations"].append(_("✓ CDN für globale Geschwindigkeit"))
                break
        
        if not result["server"]["cdn_detected"]:
            result["warnings"].append(_("⚠ Kein CDN - langsame Ladezeiten im Ausland"))
        
        # Cache Headers (max 40 Punkte)
        cache_headers = ['Cache-Control', 'ETag', 'Expires', 'Last-Modified']
        if any(h in response.headers for h in cache_headers):
            result["server"]["cache_headers"] = True
            server_score += 40
        else:
            server_score -= 10
            result["warnings"].append(_("❌ Kein Browser-Caching - wiederholte Besucher langsamer"))
        
        # HTTP/2 (max 20 Punkte)
        if response.raw.version == 20:
            server_score += 20
        else:
            result["warnings"].append(_("⚠ Kein HTTP/2 - veraltetes Protokoll"))
        
        # Server-Info (max 10 Punkte)
        if 'Server' in response.headers:
            result["server"]["server_type"] = response.headers['Server']
            server_score += 10
        
        result["server"]["score"] = max(0, min(100, server_score))
        
        # ========== MOBILE (0-100) ==========
        mobile_score = 20  # Niedrig, da Mobile-First Pflicht ist
        
        # Viewport (max 50 Punkte, kritisch)
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            result["mobile"]["viewport_meta"] = True
            mobile_score += 50
            result["recommendations"].append(_("✓ Mobile-optimiert"))
        else:
            result["warnings"].append(_("❌ NICHT MOBILFREUNDLICH! Google indexiert Mobile-First!"))
        
        # Responsive Images (max 30 Punkte)
        responsive_imgs = soup.find_all('img', attrs={'srcset': True})
        picture_tags = soup.find_all('picture')
        if responsive_imgs or picture_tags:
            result["mobile"]["responsive_images"] = True
            mobile_score += 30
        else:
            result["warnings"].append(_("⚠ Keine responsiven Bilder - Mobile-Datenverschwendung"))
        
        # Mobile Test (max 20 Punkte)
        try:
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            }
            mobile_response = requests.get(url, headers=mobile_headers, timeout=5)
            if mobile_response.status_code == 200:
                result["mobile"]["mobile_friendly"] = True
                mobile_score += 20
        except:
            pass
        
        result["mobile"]["score"] = max(0, min(100, mobile_score))
        
        # ========== ACCESSIBILITY (0-100) ==========
        accessibility_score = 30
        
        # Lang Attribute (max 30 Punkte)
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            result["accessibility"]["lang_attribute"] = True
            accessibility_score += 30
        else:
            result["warnings"].append(_("⚠ Keine Sprachangabe - Screenreader-Probleme"))
        
        # Alt-Texte (max 40 Punkte)
        if result["seo"]["total_images"] > 0:
            alt_ratio = (result["seo"]["total_images"] - result["seo"]["images_without_alt"]) / result["seo"]["total_images"]
            accessibility_score += int(alt_ratio * 40)
            if alt_ratio < 1:
                result["warnings"].append(_("⚠ Barrierefreiheit: Fehlende Alt-Texte"))
        
        result["accessibility"]["alt_texts"] = result["seo"]["total_images"] - result["seo"]["images_without_alt"]
        
        # ARIA Labels (max 30 Punkte)
        aria_elements = soup.find_all(attrs={"aria-label": True})
        result["accessibility"]["aria_labels"] = len(aria_elements)
        accessibility_score += min(30, len(aria_elements) * 3)
        
        result["accessibility"]["score"] = max(0, min(100, accessibility_score))
        
        # ========== GEWICHTETER GESAMTSCORE ==========
        # SEO stärker gewichtet, Performance etwas weniger
        weights = {
            "seo": 0.30,        # ↑ Von 25% auf 30% (wichtig für Kunden)
            "performance": 0.20, # ↓ Von 25% auf 20%
            "security": 0.20,    # Gleich (Vertrauen wichtig)
            "mobile": 0.15,      # ↑ Von 12% auf 15% (Mobile-First)
            "server": 0.10,      # Gleich
            "accessibility": 0.05 # ↓ Von 8% auf 5%
        }
        
        overall = 0
        for category, weight in weights.items():
            score = result[category]["score"]
            result["category_scores"][category] = score
            overall += score * weight
        
        result["overall_score"] = int(overall)
        
        # Finale Einordnung mit Akquise-Fokus
        if result["overall_score"] >= 75:
            result["recommendations"].insert(0, _("🎉 Sehr gute Basis - Feintuning möglich"))
        elif result["overall_score"] >= 55:
            result["recommendations"].insert(0, _("👍 Solide Basis mit Optimierungspotential"))
        elif result["overall_score"] >= 40:
            result["warnings"].insert(0, _("⚠️ Mehrere kritische Bereiche benötigen Aufmerksamkeit"))
        else:
            result["warnings"].insert(0, _("❌ DRINGENDER HANDLUNGSBEDARF - Wir können helfen!"))
        
        # Zusätzliche Verkaufsargumente bei schlechten Scores
        if result["overall_score"] < 60:
            result["warnings"].append(_("💡 Professionelle Optimierung kann Ihre Conversion-Rate deutlich steigern"))
        
        if result["seo"]["score"] < 50:
            result["warnings"].append(_("💡 SEO-Optimierung: Mehr organischer Traffic = weniger AdWords-Kosten"))
        
        if result["performance"]["score"] < 50:
            result["warnings"].append(_("💡 Jede Sekunde Ladezeit kostet ca. 7% Conversions"))
        
    except requests.exceptions.Timeout:
        result["error"] = _("Timeout - Server reagiert nicht")
    except requests.exceptions.SSLError:
        result["error"] = _("SSL-Fehler - Zertifikat ungültig")
    except requests.exceptions.ConnectionError:
        result["error"] = _("Verbindungsfehler - Website nicht erreichbar")
    except Exception as e:
        result["error"] = _(f"Fehler: {str(e)}")
    
    return result


def send_test_results_email(email, result):
    """Sendet Ergebnisse mit Fokus auf Conversion-Optimierung."""
    try:
        subject = f"Ihre Website-Analyse: {result['overall_score']}/100 Punkten - Optimierungspotential erkannt"
        
        def get_score_color(score):
            if score >= 75: return '#10b981'
            elif score >= 55: return '#3b82f6'
            elif score >= 40: return '#f59e0b'
            else: return '#ef4444'
        
        def get_score_gradient(score):
            if score >= 75: return 'linear-gradient(135deg, #10b981, #059669)'
            elif score >= 55: return 'linear-gradient(135deg, #3b82f6, #2563eb)'
            elif score >= 40: return 'linear-gradient(135deg, #f59e0b, #d97706)'
            else: return 'linear-gradient(135deg, #ef4444, #dc2626)'
        
        def get_score_label(score):
            if score >= 75: return 'Sehr gut'
            elif score >= 55: return 'Optimierungspotential'
            elif score >= 40: return 'Handlungsbedarf'
            else: return 'Dringend optimieren'
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Website-Analyse Ergebnis</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #ffffff;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="text-align: center; padding-bottom: 30px;">
                                    <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 800;">Ihre Website-Analyse</h1>
                                    <p style="color: #a0a0a0; font-size: 14px; margin: 10px 0 0 0;">{{ url }}</p>
                                </td>
                            </tr>
                            
                            <!-- Score Circle -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #1a1a1a, #0f0f0f); border-radius: 20px; padding: 40px; text-align: center; border: 1px solid #2a2a2a;">
                                    <div style="width: 160px; height: 160px; border-radius: 50%; margin: 0 auto 20px; background: {{ score_gradient }}; padding: 10px; box-shadow: 0 0 50px {{ score_color }}30;">
                                        <div style="width: 140px; height: 140px; border-radius: 50%; background: #0a0a0a; display: flex; align-items: center; justify-content: center; flex-direction: center; margin: 10px;">
                                            <div style="text-align: center;">
                                                <div style="font-size: 52px; font-weight: 800; color: {{ score_color }}; line-height: 1;">{{ overall_score }}</div>
                                                <div style="font-size: 14px; color: #666; margin-top: 5px;">/ 100</div>
                                            </div>
                                        </div>
                                    </div>
                                    <h2 style="color: {{ score_color }}; font-size: 24px; margin: 0 0 10px 0; font-weight: 700;">{{ score_label }}</h2>
                                    <p style="color: #a0a0a0; font-size: 16px; margin: 0; line-height: 1.6;">
                                        {% if overall_score < 60 %}
                                        Ihre Website hat Optimierungspotential. Wir zeigen Ihnen, wie Sie mehr aus ihr herausholen können.
                                        {% else %}
                                        Gute Basis! Hier sind Details zu Ihren Stärken und Optimierungsmöglichkeiten.
                                        {% endif %}
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Category Scores -->
                            <tr>
                                <td style="padding-top: 30px;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td width="48%" style="background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #2a2a2a; border-top: 3px solid {{ seo_color }};">
                                                <p style="color: #a0a0a0; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 0.5px;">SEO (wichtig)</p>
                                                <p style="color: {{ seo_color }}; font-size: 32px; font-weight: 800; margin: 0;">{{ seo_score }}<span style="font-size: 16px; color: #666; font-weight: 400;">/100</span></p>
                                            </td>
                                            <td width="4%"></td>
                                            <td width="48%" style="background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #2a2a2a; border-top: 3px solid {{ performance_color }};">
                                                <p style="color: #a0a0a0; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 0.5px;">Performance</p>
                                                <p style="color: {{ performance_color }}; font-size: 32px; font-weight: 800; margin: 0;">{{ performance_score }}<span style="font-size: 16px; color: #666; font-weight: 400;">/100</span></p>
                                            </td>
                                        </tr>
                                        <tr><td height="15"></td></tr>
                                        <tr>
                                            <td width="48%" style="background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #2a2a2a; border-top: 3px solid {{ security_color }};">
                                                <p style="color: #a0a0a0; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 0.5px;">Sicherheit</p>
                                                <p style="color: {{ security_color }}; font-size: 32px; font-weight: 800; margin: 0;">{{ security_score }}<span style="font-size: 16px; color: #666; font-weight: 400;">/100</span></p>
                                            </td>
                                            <td width="4%"></td>
                                            <td width="48%" style="background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #2a2a2a; border-top: 3px solid {{ mobile_color }};">
                                                <p style="color: #a0a0a0; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 0.5px;">Mobile</p>
                                                <p style="color: {{ mobile_color }}; font-size: 32px; font-weight: 800; margin: 0;">{{ mobile_score }}<span style="font-size: 16px; color: #666; font-weight: 400;">/100</span></p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Critical Metrics -->
                            <tr>
                                <td style="padding-top: 30px;">
                                    <h3 style="color: #ffffff; font-size: 18px; margin: 0 0 15px 0;">Wichtige Kennzahlen</h3>
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: #1a1a1a; border-radius: 12px; border: 1px solid #2a2a2a;">
                                        <tr>
                                            <td style="padding: 15px 20px; border-bottom: 1px solid #2a2a2a;">
                                                <span style="color: #a0a0a0; font-size: 14px;">Ladezeit</span>
                                                <span style="color: #ffffff; font-size: 16px; font-weight: 600; float: right;">{{ response_time }}ms</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 20px; border-bottom: 1px solid #2a2a2a;">
                                                <span style="color: #a0a0a0; font-size: 14px;">Seitengröße</span>
                                                <span style="color: #ffffff; font-size: 16px; font-weight: 600; float: right;">{{ page_size }}</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 20px; border-bottom: 1px solid #2a2a2a;">
                                                <span style="color: #a0a0a0; font-size: 14px;">Google-Rankingfaktoren</span>
                                                <span style="color: {{ seo_color }}; font-size: 16px; font-weight: 600; float: right;">{{ seo_score }}% optimiert</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 20px;">
                                                <span style="color: #a0a0a0; font-size: 14px;">Sicherheit (SSL)</span>
                                                <span style="color: {{ ssl_color }}; font-size: 16px; font-weight: 600; float: right;">{{ ssl_status }}</span>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Warnings (Prioritized) -->
                            {% if warnings %}
                            <tr>
                                <td style="padding-top: 30px;">
                                    <h3 style="color: #f59e0b; font-size: 18px; margin: 0 0 15px 0;">⚠ Optimierungspotential</h3>
                                    {% for warn in warnings %}
                                    <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; padding: 14px 16px; margin-bottom: 10px; border-radius: 0 10px 10px 0; color: #fef3c7; font-size: 14px; line-height: 1.5;">
                                        {{ warn }}
                                    </div>
                                    {% endfor %}
                                </td>
                            </tr>
                            {% endif %}
                            
                            <!-- CTA Section -->
                            <tr>
                                <td style="padding-top: 40px;">
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; padding: 30px; text-align: center;">
                                        <h3 style="color: white; font-size: 20px; margin: 0 0 10px 0; font-weight: 700;">Bereit für mehr Performance?</h3>
                                        <p style="color: rgba(255,255,255,0.9); font-size: 15px; margin: 0 0 20px 0; line-height: 1.5;">
                                            Wir helfen Ihnen, das volle Potential Ihrer Website auszuschöpfen. Kostenloses Erstgespräch.
                                        </p>
                                        <a href="{{ site_url }}/termin/" style="display: inline-block; background: white; color: #667eea; padding: 14px 28px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">Kostenlosen Termin vereinbaren</a>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding-top: 40px; text-align: center; border-top: 1px solid #2a2a2a; margin-top: 40px;">
                                    <p style="color: #666; font-size: 12px; margin: 0;">© 2025 Joel Digitals</p>
                                    <p style="color: #666; font-size: 12px; margin: 5px 0 0 0;">Analyse vom {{ test_date }}</p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        template = Template(html_template)
        context = Context({
            'url': result['url'],
            'test_date': result['test_date'],
            'overall_score': result['overall_score'],
            'score_color': get_score_color(result['overall_score']),
            'score_gradient': get_score_gradient(result['overall_score']),
            'score_label': get_score_label(result['overall_score']),
            'performance_score': result['category_scores'].get('performance', 0),
            'performance_color': get_score_color(result['category_scores'].get('performance', 0)),
            'seo_score': result['category_scores'].get('seo', 0),
            'seo_color': get_score_color(result['category_scores'].get('seo', 0)),
            'security_score': result['category_scores'].get('security', 0),
            'security_color': get_score_color(result['category_scores'].get('security', 0)),
            'mobile_score': result['category_scores'].get('mobile', 0),
            'mobile_color': get_score_color(result['category_scores'].get('mobile', 0)),
            'response_time': result['performance']['response_time'],
            'page_size': f"{round(result['performance']['page_size'] / 1024, 1)} KB",
            'ssl_status': 'Aktiv' if result['security']['ssl_valid'] else 'Fehlt',
            'ssl_color': '#10b981' if result['security']['ssl_valid'] else '#ef4444',
            'warnings': result['warnings'][:8],
            'site_url': getattr(settings, 'SITE_URL', 'https://joeldigitals.de')
        })
        
        html_content = template.render(context)
        
        # Plain text - ohne f-string mit Template-Syntax
        cta_text = ""
        if result['overall_score'] < 70:
            cta_text = """
PROFESSIONELLE OPTIMIERUNG EMPFOHLEN
Steigern Sie Ihre Conversion-Rate und reduzieren Sie AdWords-Kosten durch besseres SEO.

Kostenloses Beratungsgespräch:
""" + getattr(settings, 'SITE_URL', 'https://joeldigitals.de') + "/termin/"
        
        text_content = f"""Ihre Website-Analyse für {result['url']}
========================================

GESAMTERGEBNIS: {result['overall_score']}/100 Punkten

DETAILAUSWERTUNG:
• SEO (Google-Optimierung): {result['category_scores'].get('seo', 0)}/100
• Performance (Ladezeit): {result['category_scores'].get('performance', 0)}/100  
• Sicherheit: {result['category_scores'].get('security', 0)}/100
• Mobile Optimierung: {result['category_scores'].get('mobile', 0)}/100

WICHTIGE FINDINGS:
""" + chr(10).join('• ' + w for w in result['warnings'][:5]) + cta_text + """

---
Joel Digitals | """ + getattr(settings, 'SITE_URL', 'https://joeldigitals.de')
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@joeldigitals.de'),
            to=[email],
            reply_to=[getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@joeldigitals.de')]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        import traceback
        traceback.print_exc()
        return False