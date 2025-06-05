from django.urls import path
from . import views

app_name = 'wiki'

urlpatterns = [
    path('', views.wiki_overview, name='overview'),
    path('<slug:slug>/', views.wiki_detail, name='detail'),
    path('language/<str:lang>/', views.set_language, name='set_language'),
]
