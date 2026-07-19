# jds_configurator/urls.py
from django.urls import path
from . import views
from . import admin_views

app_name = 'jds_configurator'

urlpatterns = [
    path('', views.wizard, name='wizard'),
    path('angebot/pdf/', views.download_offer_pdf, name='download_offer_pdf'),
    path('anfragen/', views.submit_request, name='submit_request'),
    path('warenkorb/hinzufuegen/', views.add_to_cart, name='add_to_cart'),
    path('funktionswunsch/', views.submit_feature_request, name='submit_feature_request'),

    # Plattform-Admin: Genehmigung der Anfragen
    path('admin/anfragen/', admin_views.request_list, name='admin_request_list'),
    path('admin/anfragen/<int:pk>/', admin_views.request_detail, name='admin_request_detail'),
    path('admin/anfragen/<int:pk>/approve/', admin_views.request_approve, name='admin_request_approve'),
    path('admin/anfragen/<int:pk>/reject/', admin_views.request_reject, name='admin_request_reject'),

    # Plattform-Admin: individuelle Funktionswünsche
    path('admin/funktionswuensche/', admin_views.feature_request_list, name='admin_feature_request_list'),
    path('admin/funktionswuensche/<int:pk>/', admin_views.feature_request_detail, name='admin_feature_request_detail'),
    path('admin/funktionswuensche/<int:pk>/approve/', admin_views.feature_request_approve, name='admin_feature_request_approve'),
    path('admin/funktionswuensche/<int:pk>/reject/', admin_views.feature_request_reject, name='admin_feature_request_reject'),
    path('admin/funktionswuensche/<int:pk>/in-pruefung/', admin_views.feature_request_mark_in_review, name='admin_feature_request_in_review'),
]
