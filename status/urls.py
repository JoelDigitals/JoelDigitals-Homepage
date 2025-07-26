from django.urls import path
from . import views

urlpatterns = [
    path('', views.status_overview, name='status_overview'),
    path('app/<int:app_id>/', views.app_detail, name='app_detail'),
]
