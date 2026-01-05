# landingpages/urls.py
from django.urls import path
from .views import landing_page_view

urlpatterns = [
    path('<slug:slug>/', landing_page_view, name='landing_page'),
]
