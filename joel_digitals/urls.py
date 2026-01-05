"""
URL configuration for joel_digitals project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from main.sitemaps import StaticViewSitemap  # gleich erstellen!

# --- Sitemap Definition ---
sitemaps = {
    'static': StaticViewSitemap,
}

# --- Basis-URL-Muster (nicht sprachabhängig) ---
urlpatterns = [
    # Sitemap soll außerhalb von /de/ oder /en/ liegen
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Optional: Sprachumschaltung soll auch ohne Sprache funktionieren
    path("i18n/", include("django.conf.urls.i18n")),
]

# --- Sprachabhängige URLs (z. B. /de/ oder /en/) ---
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('auth/', include('main.urls_auth')),
    path('', include('main.urls')),
    path('blog/', include('blog.urls')),
    path('contact/', include('contact.urls')),
    path('', include('shop_ourapps.urls')),  # dein Shop
    path('wiki/', include('wiki.urls')),
    path('status/', include('status.urls')),
    path('downloads/', include('download.urls')),
    path('mobile/', include('MobileApp.urls')),
    path('chat/', include('chat.urls')),  # Pfad bleibt /de/chat/api/
    path("reviews/", include("reviews.urls")),
    # project urls.py
    path('', include('landingpages.urls')),
    
)

# --- Medien-Dateien ---
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
