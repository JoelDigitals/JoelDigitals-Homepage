from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('imprint/', views.imprint_view, name='imprint'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('services/', views.service_view, name='services'),
    path('about/', views.about_view, name='about'),
]
