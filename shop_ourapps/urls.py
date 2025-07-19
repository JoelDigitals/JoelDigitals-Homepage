from django.urls import path
from . import views

urlpatterns = [
    path('our-apps/', views.our_apps, name='our_apps'),
    path('our-apps/<slug:slug>/', views.more_informations, name='more_information'),
    path('shop/', views.shop, name='shop'),
    path('shop/voucher/', views.buy_voucher, name='buy_voucher'),
    path('shop/<slug:slug>/', views.app_detail, name='app_detail'),
    
    path('shop/<slug:slug>/buy/', views.purchase_app, name='purchase_app'),
    path('affiliate/dashboard/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/eligibility/', views.affiliate_eligibility, name='affiliate_eligibility'),
    path('wallet/', views.wallet_view, name='wallet'),

    # Weitere URLs für das Shop-System (Warenkorb und Checkout)
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:app_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path("checkout/validate-codes/", views.validate_codes, name="validate_codes"),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
]
