from django.urls import path
from . import views

urlpatterns = [
    path('our-apps/', views.our_apps, name='our_apps'),
    path('our-apps/<slug:slug>/', views.more_informations, name='more_information'),
    path('shop/', views.shop, name='shop'),
    path('shop/voucher/', views.buy_voucher, name='buy_voucher'),
    path('voucher/success/<int:voucher_id>/', views.voucher_success, name='voucher_success'),
    path('shop/<slug:slug>/', views.app_detail, name='app_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<int:order_id>/', views.my_order_detail, name='order_detail'),
    path('my-orders/<int:order_id>/invoice/', views.invoice_view, name='invoice'),
    path('my-orders/<int:order_id>/invoice/download/', views.invoice_pdf, name='download_invoice'),
    
    path('shop/<slug:slug>/buy/', views.purchase_app, name='purchase_app'),
    path("affiliate/info/", views.affiliate_info, name="affiliate_info"),
    path('affiliate/dashboard/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/eligibility/', views.affiliate_eligibility, name='affiliate_eligibility'),
    path('wallet/', views.wallet_view, name='wallet'),

    # Weitere URLs für das Shop-System (Warenkorb und Checkout)
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:app_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path("create-stripe-payment/<int:order_id>/", views.create_stripe_payment, name="create_stripe_payment"),
    path('paypal/execute/', views.paypal_execute, name='paypal_execute'),
    path("checkout/validate-codes/", views.validate_codes, name="validate_codes"),
    path("api/validate-affiliate/", views.validate_affiliate_code, name="validate_affiliate_code"),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    path('admin-sales/orders/', views.order_admin, name='order_admin'),
    path('admin-sales/create-order/', views.admin_create_order, name='admin_create_order'),
    path('admin-sales/search-users/', views.admin_search_users, name='admin_search_users'),
    path('my-orders/<int:order_id>/return/', views.request_return, name='request_return'),
    path('my-orders/<int:order_id>/tracking/', views.order_tracking, name='order_tracking'),
    path('admin-sales/orders/<int:order_id>/set-tracking/', views.order_admin_set_tracking, name='order_admin_set_tracking'),
    path('my-orders/return/<int:return_id>/print/', views.return_label_print, name='return_label_print'),
    path('admin-sales/return/<int:return_id>/print/', views.return_label_print_admin, name='return_label_print_admin'),

    # Bewertungen
    path('shop/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('shop/<slug:slug>/review/delete/', views.delete_review, name='delete_review'),

    # Stripe Webhook (in settings: STRIPE_WEBHOOK_SECRET)
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

    # Fast-Cron Endpoint — alle 5 Min aufrufen
    # Optional: ?token=CRON_SECRET in settings.py absichern
    path('shop/status/emails/corn/', views.email_cron, name='email_cron'),
    path('lp/<str:username>/<slug:product_slug>/', views.personalized_landing, name='personalized_landing'),
    path('lp/<slug:product_slug>/', views.product_landing, name='product_landing'),
    path('go/<slug:slug>/', views.custom_landing, name='custom_landing'),
    path('withdrawal/', views.withdrawal_form, name='withdrawal_form'),
]