from django.urls import path

from . import views

urlpatterns = [
    path('', views.jd_home_app, name='jd_home_app'),
    path('login/', views.jd_login_app, name='jd_login_app'),
    path('register/', views.jd_register_app, name='jd_register_app'),
    path('logout/', views.jd_logout_app, name='jd_logout_app'),
    path('deals/', views.jd_deals_app, name='jd_deals_app'),
    path('articles/', views.jd_articles_app, name='jd_articles_app'),
    path('orders/', views.jd_orders_app, name='jd_orders_app'),
    path('orders/<int:order_id>/', views.jd_order_detail_app, name='jd_order_detail_app'),
    path('orders/<int:order_id>/callback/', views.jd_request_callback_app, name='jd_request_callback_app'),
    path('orders/<int:order_id>/return/', views.jd_request_return_app, name='jd_request_return_app'),
    path('admin-dashboard/', views.jd_admin_dashboard_app, name='jd_admin_dashboard_app'),
    path('status/', views.jd_status_app, name='jd_status_app'),
    path('support/', views.jd_support_app, name='jd_support_app'),
    path('support/<str:ticket_number>/', views.jd_ticket_detail_app, name='jd_ticket_detail_app'),
    path('admin-blog/', views.jd_blog_admin_app, name='jd_blog_admin_app'),
    path('admin-blog/create/', views.jd_blog_create_app, name='jd_blog_create_app'),
    path('admin-newsletter/', views.jd_newsletter_app, name='jd_newsletter_app'),
    path('admin-orders/', views.jd_order_admin_app, name='jd_order_admin_app'),
    path('admin-orders/create/', views.jd_new_order_app, name='jd_new_order_app'),
    path('tools/', views.jd_tools_app, name='jd_tools_app'),
    path('wallet/', views.jd_wallet_app, name='jd_wallet_app'),
    path('affiliate/', views.jd_affiliate_dashboard_app, name='jd_affiliate_dashboard_app'),
    path('profile/', views.jd_profile_app, name='jd_profile_app'),
    path('profile/edit/', views.jd_profile_edit_app, name='jd_profile_edit_app'),
    path('profile/change-password/', views.jd_change_password_app, name='jd_change_password_app'),
    path('settings/', views.jd_settings_app, name='jd_settings_app'),
    path('settings/status-subscriptions/<int:app_id>/toggle/', views.jd_toggle_status_subscription_app, name='jd_toggle_status_subscription_app'),
    path('settings/push-notifications/toggle/', views.jd_toggle_push_notifications_app, name='jd_toggle_push_notifications_app'),
    path('settings/app-permissions/', views.jd_app_permissions_app, name='jd_app_permissions_app'),
    path('settings/delete-account/', views.jd_delete_account_app, name='jd_delete_account_app'),
    path('api/save-onesignal/', views.jd_save_onesignal_player_id_app, name='jd_save_onesignal_player_id_app'),

    # Shop im App-Design
    path('shop/', views.jd_shop_app, name='jd_shop_app'),
    path('shop/<slug:slug>/', views.jd_app_detail_app, name='jd_app_detail_app'),
    path('cart/', views.jd_cart_app, name='jd_cart_app'),
    path('checkout/', views.jd_checkout_app, name='jd_checkout_app'),
    path('orders/confirmation/<int:order_id>/', views.jd_order_confirmation_app, name='jd_order_confirmation_app'),
    path('orders/<int:order_id>/invoice/', views.jd_invoice_view_app, name='jd_invoice_view_app'),
    path('cart/add/<int:app_id>/', views.jd_add_to_cart_app, name='jd_add_to_cart_app'),
    path('cart/remove/<int:item_id>/', views.jd_remove_from_cart_app, name='jd_remove_from_cart_app'),

    # Termine
    path('appointment/', views.jd_appointment_app, name='jds_appointment_app'),
    path('appointment/success/', views.jd_appointment_success_app, name='jd_appointment_success_app'),
    path('admin-appointments/', views.jd_admin_appointments_app, name='jd_admin_appointments_app'),
    path('admin-appointments/update/<int:pk>/<str:status>/', views.jd_update_appointment_status_app, name='jd_update_appointment_status_app'),

    # Support-Ticket-Verwaltung (Admin)
    path('admin-tickets/', views.jd_admin_tickets_app, name='jd_admin_tickets_app'),
    path('admin-tickets/archive/', views.jd_ticket_archive_app, name='jd_ticket_archive_app'),
    path('admin-tickets/archive/<str:ticket_number>/', views.jd_archived_ticket_detail_app, name='jd_archived_ticket_detail_app'),

    # Website-Konfigurator-Leads (Admin)
    path('admin-website-requests/', views.jd_website_config_list_app, name='jd_website_config_list_app'),
    path('admin-website-requests/archive/', views.jd_website_config_archive_app, name='jd_website_config_archive_app'),
    path('admin-website-requests/<int:pk>/', views.jd_website_config_detail_app, name='jd_website_config_detail_app'),
    path('admin-website-requests/<int:pk>/status/', views.jd_website_config_update_status_app, name='jd_website_config_update_status_app'),
    path('admin-website-requests/<int:pk>/mail/', views.jd_website_config_send_mail_app, name='jd_website_config_send_mail_app'),

    # Sales-Verwaltung (Admin) inkl. Chat
    path('admin-sales/', views.jd_admin_sales_app, name='jds_admin_sales_app'),
    path('admin-sales/<int:entry_id>/', views.jd_sales_entry_detail_app, name='jd_sales_entry_detail_app'),
    path('admin-sales/<int:entry_id>/chat/', views.jd_sales_chat_app, name='jd_sales_chat_app'),
    path('admin-sales/<int:entry_id>/add/', views.jd_add_wish_app, name='jd_add_wish_app'),
    path('admin-sales/<int:entry_id>/edit/<int:wish_id>/', views.jd_edit_wish_app, name='jd_edit_wish_app'),
    path('admin-sales/<int:entry_id>/delete/<int:wish_id>/', views.jd_delete_wish_app, name='jd_delete_wish_app'),
    path('admin-sales/<int:entry_id>/export/<int:wish_id>/', views.jd_export_single_wish_app, name='jd_export_single_wish_app'),
]
