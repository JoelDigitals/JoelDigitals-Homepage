from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='contactz_home'),
    path('contact/', views.contact_view, name='contact_form'),
    path('sales/', views.sales, name='sales'),
    path('sales/chat/<int:entry_id>/', views.sales_chat, name='sales_chat'),
    path('sales/export/', views.export_wishes, name='export_wishes'),
    path('support/', views.support_tickets, name='support_tickets'),
    path('support/<str:ticket_number>/', views.ticket_detail, name='ticket_detail'),
    path('admin-tickets/', views.admin_ticket_view, name='admin_tickets'),
    path('admin-sales/', views.admin_sales_view, name='admin_sales'),
    path('admin-sales/<int:entry_id>/', views.sales_entry_detail, name='sales_entry_detail'),
    path('admin-sales/<int:entry_id>/add/', views.add_wish, name='add_wish'),
    path('admin-sales/<int:entry_id>/edit/<int:wish_id>/', views.edit_wish, name='edit_wish'),
    path('admin-sales/<int:entry_id>/delete/<int:wish_id>/', views.delete_wish, name='delete_wish'),
    path('admin-sales/<int:entry_id>/export/<int:wish_id>/', views.export_single_wish, name='export_single_wish'),

]
