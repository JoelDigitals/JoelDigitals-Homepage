from django.urls import path
from . import views

app_name = 'webinars'

urlpatterns = [
    path('', views.webinar_list, name='webinar_list'),
    path('<slug:slug>/', views.webinar_detail, name='webinar_detail'),
    path('<slug:slug>/register/', views.webinar_register, name='webinar_register'),
    path('<slug:slug>/cancel/', views.webinar_cancel, name='webinar_cancel'),
]
