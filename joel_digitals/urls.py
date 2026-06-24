"""
URL configuration for joel_digitals project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from main.sitemaps import StaticViewSitemap, BlogSitemap, LandingPageSitemap, ShopAppSitemap, WikiSitemap
from main import views as main_views  # ← WICHTIG: Import hinzufügen

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
    path('chat/', include('chat.urls')),
    path("reviews/", include("reviews.urls")),
    path('api/autoupdate/', include('autoupdate.urls')),
    path('', include('landingpages.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
)

# --- Medien-Dateien ---
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)