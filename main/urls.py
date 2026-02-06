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
]
