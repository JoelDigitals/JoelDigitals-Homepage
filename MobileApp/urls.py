from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view_app, name='login_app'),
    path('logout/', views.logout_view_app, name='logout_app'),
    path('', views.home_view_app, name='home_app'),
    path('sales/', views.sales_app, name='sales_app'),
    path('sales/chat/<int:entry_id>/', views.sales_chat_app, name='sales_chat_app'),
    path('sales/export/', views.export_wishes_app, name='export_wishes_app'),
    path('support/', views.support_tickets_app, name='support_tickets_app'),
    path('support/<str:ticket_number>/', views.ticket_detail_app, name='ticket_detail_app'),
    path('admin-tickets/', views.admin_ticket_view_app, name='admin_tickets_app'),
    path('admin-tickets/archive/', views.ticket_archive_view_app, name='archive_ticket_app'),
    path('admin-tickets/archive/<str:ticket_number>/', views.ticket_detail_view_app, name='admin_ticket_detail_app'),
    path('admin-sales/', views.admin_sales_view_app, name='admin_sales_app'),
    path('admin-sales/<int:entry_id>/', views.sales_entry_detail_app, name='sales_entry_detail_app'),
    path('admin-sales/<int:entry_id>/add/', views.add_wish_app, name='add_wish_app'),
    path('admin-sales/<int:entry_id>/edit/<int:wish_id>/', views.edit_wish_app, name='edit_wish_app'),
    path('admin-sales/<int:entry_id>/delete/<int:wish_id>/', views.delete_wish_app, name='delete_wish_app'),
    path('admin-sales/<int:entry_id>/export/<int:wish_id>/', views.export_single_wish_app, name='export_single_wish_app'),
]
