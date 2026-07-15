"""
URL configuration for joel_digitals project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve as static_serve
from django.contrib.sitemaps.views import sitemap
from main.sitemaps import StaticViewSitemap, BlogSitemap, LandingPageSitemap, ShopAppSitemap, WikiSitemap
from main import views as main_views  # ← WICHTIG: Import hinzufügen
from JoelDigitalsApp import cron as jd_cron
from JoelDigitalsApp import views as jd_views
from django.views.generic import TemplateView

# --- Sitemap Definition ---
sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'landingpages': LandingPageSitemap,
    'shop': ShopAppSitemap,
    'wiki': WikiSitemap,
}

# --- Basis-URL-Muster (nicht sprachabhängig) ---
urlpatterns = [
    # Sitemap soll außerhalb von /de/ oder /en/ liegen
    
    path('auth/sso/connect/', main_views.sso_connect, name='sso_connect'),
    path('auth/sso/connect/login/', main_views.sso_connect_login, name='sso_connect_login'),
    path('api/sso/validate/', main_views.validate_sso_token, name='sso_validate'),
    path('auth/sso/login/', main_views.sso_login_page, name='sso_login_page'),
    path('auth/sso/authorize-page/', main_views.sso_authorize_page, name='sso_authorize_page'),
    path('auth/sso/authorize/', main_views.sso_authorize, name='sso_authorize'),
    path('auth/sso/validate/', main_views.validate_sso_token, name='validate_sso_token'),
    path('api/admin/', include('admin_api.urls')),
    path('robots.txt', main_views.robots_txt),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap.txt', main_views.sitemap_txt, name='sitemap_txt'),
    # Optional: Sprachumschaltung soll auch ohne Sprache funktionieren
    path("i18n/", include("django.conf.urls.i18n")),

    # Auto-Update-API fuer JDS Secure: bewusst NICHT hinter i18n_patterns,
    # da es sich um einen Maschinen-Client (PowerShell/.NET) ohne Sprachpraefix
    # handelt. Innerhalb von i18n_patterns wuerde jede Anfrage ohne /de/-Praefix
    # per 302 umgeleitet statt direkt beantwortet zu werden.
    path('api/autoupdate/', include('autoupdate.urls')),

    # Push-Cron fuer die Joel Digitals App (z.B. FastCron ruft diese URL alle
    # paar Minuten auf) - aus demselben Grund wie oben bewusst NICHT hinter
    # i18n_patterns.
    path('api/push-check/', jd_cron.push_check, name='jd_push_check'),

    # OneSignal Service Worker – MUSS auf der Root-Ebene liegen, da der
    # Browser ihn fuer Push-Benachrichtigungen unter dieser exakten URL
    # registriert. Darf NICHT in i18n_patterns liegen.
    path('OneSignalSDKWorker.js', TemplateView.as_view(
        template_name='OneSignalSDKWorker.js',
        content_type='application/javascript',
    )),

    # Firebase-Messaging-Service-Worker - MUSS ebenfalls auf Root-Ebene liegen
    # (Browser registriert den Push-Scope relativ zur Service-Worker-URL).
    # Darf NICHT in i18n_patterns liegen.
    path('firebase-messaging-sw.js', jd_views.firebase_messaging_sw, name='firebase_messaging_sw'),

    # Downloadbare Update-Pakete: django.conf.urls.static.static() dient nur
    # im DEBUG-Modus, wird also in Produktion (DEBUG=False) NICHT registriert.
    # Der JDS-Secure-Client braucht diese Downloads aber auch im Live-Betrieb,
    # daher hier bewusst und eng auf media/autoupdate/ begrenzt ausliefern
    # (nicht das komplette MEDIA_ROOT), unabhaengig vom DEBUG-Wert.
    path(
        'media/autoupdate/<path:path>',
        static_serve,
        {'document_root': str(settings.MEDIA_ROOT / 'autoupdate')},
    ),

    # ==================== SSO URLs (OHNE i18n) ===================
    # ============================================================
]

# --- Sprachabhängige URLs (z. B. /de/ oder /en/) ---
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('auth/', include('main.urls_auth')),
    path('', include('main.urls')),
    path('blog/', include('blog.urls')),
    path('contact/', include('contact.urls')),
    path('', include('shop_ourapps.urls')),
    path('wiki/', include('wiki.urls')),
    path('status/', include('status.urls')),
    path('downloads/', include('download.urls')),
    path('paid-downloads/', include('download.paid_urls')),
    path('mobile/', include('MobileApp.urls')),
    path('app/', include('JoelDigitalsApp.urls')),
    path('chat/', include('chat.urls')),
    path("reviews/", include("reviews.urls")),
    path('webinars/', include('webinars.urls')),
    path('', include('landingpages.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
)

# --- Medien-Dateien ---
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)