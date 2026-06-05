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
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('profile/app-permissions/', views.app_permissions, name='app_permissions'),
    path('profile/app-permissions/revoke/<int:auth_id>/', views.revoke_app_permission, name='revoke_app_permission'),

    path('support/', views.support_view, name='support'),

    # SSO-URLs entfernt - sind jetzt in joel_digitals/urls.py
    # path('auth/sso/connect/', views.sso_connect, name='sso_connect'),
    # path('auth/sso/connect/login/', views.sso_connect_login, name='sso_connect_login'),
    # path('api/sso/validate/', views.validate_sso_token, name='sso_validate'),
]