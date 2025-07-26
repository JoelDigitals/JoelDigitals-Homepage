from django.urls import path
from . import views

urlpatterns = [
    path('', views.app_list, name='download_app_list'),
    path('app/<int:app_id>/', views.app_detail, name='download_app_detail'),
]
