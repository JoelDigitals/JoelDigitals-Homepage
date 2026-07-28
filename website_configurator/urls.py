# website_configurator/urls.py
from django.urls import path
from . import views
from . import admin_views

app_name = 'website_configurator'

urlpatterns = [
    path('', views.wizard, name='wizard'),
    path('schritt/kontakt/', views.save_contact, name='save_contact'),
    path('schritt/<int:pk>/aktualisieren/', views.update_draft, name='update_draft'),
    path('angebot/pdf/', views.download_offer_pdf, name='download_offer_pdf'),
    path('anfrage/', views.submit_request, name='submit_request'),

    # Plattform-Admin: Sichtung der Leads
    path('admin/anfragen/', admin_views.request_list, name='admin_request_list'),
    path('admin/anfragen/archiv/', admin_views.request_archive, name='admin_request_archive'),
    path('admin/anfragen/<int:pk>/', admin_views.request_detail, name='admin_request_detail'),
    path('admin/anfragen/<int:pk>/status/', admin_views.request_update_status, name='admin_request_update_status'),
    path('admin/anfragen/<int:pk>/mail/', admin_views.request_send_mail, name='admin_request_send_mail'),
]
