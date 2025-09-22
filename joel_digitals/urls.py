"""
URL configuration for joel_digitals project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

# i18n URLS für die Sprachumschaltung
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # <--- wichtig für Flaggen-Formular
]

# Alle "normalen" URLs in i18n_patterns packen
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
)

# Medien-Dateien
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
