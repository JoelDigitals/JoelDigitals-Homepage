from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('imprint/', views.imprint_view, name='imprint'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('services/', views.service_view, name='services'),
    path('about/', views.about_view, name='about'),
    path('team/', views.team_view, name='team'),
    path('accounts/login/', views.login_view, name='login'),
    path('opening-hours/', views.opening_hours, name='opening_hours'),
    path("faq/", views.faq_list, name="list"),
    path("faq/<slug:slug>/", views.faq_detail, name="detail"),
    path('api/user/', views.user_info),

    # SSO-URLs entfernt - sind jetzt in joel_digitals/urls.py
    # path('auth/sso/connect/', views.sso_connect, name='sso_connect'),
    # path('auth/sso/connect/login/', views.sso_connect_login, name='sso_connect_login'),
    # path('api/sso/validate/', views.validate_sso_token, name='sso_validate'),
]