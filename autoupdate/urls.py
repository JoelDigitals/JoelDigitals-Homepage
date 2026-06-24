from django.urls import path
from . import views

urlpatterns = [
    path('apps/', views.app_list, name='autoupdate_app_list'),
    path('check/<slug:app_slug>/', views.check_version, name='autoupdate_check'),
    path('versions/<slug:app_slug>/', views.all_versions, name='autoupdate_versions'),
]
