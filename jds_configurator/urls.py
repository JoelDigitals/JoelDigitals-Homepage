# jds_configurator/urls.py
from django.urls import path
from . import views
from . import admin_views

app_name = 'jds_configurator'

urlpatterns = [
    path('', views.wizard, name='wizard'),
    path('discount/validate/', views.validate_discount, name='validate_discount'),
    path('angebot/pdf/', views.download_offer_pdf, name='download_offer_pdf'),
    path('anfragen/', views.submit_request, name='submit_request'),

    # Plattform-Admin: Genehmigung der Anfragen
    path('admin/anfragen/', admin_views.request_list, name='admin_request_list'),
    path('admin/anfragen/<int:pk>/', admin_views.request_detail, name='admin_request_detail'),
    path('admin/anfragen/<int:pk>/approve/', admin_views.request_approve, name='admin_request_approve'),
    path('admin/anfragen/<int:pk>/reject/', admin_views.request_reject, name='admin_request_reject'),
]
