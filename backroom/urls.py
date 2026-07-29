from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='backroom_list'),
    path('zugang/', views.access_request, name='backroom_access_request'),
    path('<slug:slug>/', views.product_detail, name='backroom_detail'),
]
