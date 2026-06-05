from django.contrib import admin
from .models import (
    Purchase, AffiliateLink, Affiliate, App, Cart, CartItem, AffiliateTransaction, 
    AffiliatePartner, Order, OrderItem, AffiliateCode, DiscountCode, Wallet, WalletCode, 
    AppGroup, Voucher, VoucherOrder, SaleBadge, OrderStatusLog
)

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'app', 'affiliate', 'date', 'full_name', 'email']
    list_filter = ['affiliate', 'app', 'date']

class AffiliateAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'commission_percent']
    search_fields = ['user__username', 'code']

class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ['order', 'event_type', 'old_status', 'new_status', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['order__id']
    readonly_fields = ['created_at', 'order', 'event_type', 'old_status', 'new_status', 'note']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'email', 'status', 'total_amount', 'created_at', 'registration_code_sent_at']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['first_name', 'last_name', 'email', 'id']
    readonly_fields = ['delivered_at', 'registration_code_sent_at', 'review_email_sent_at', 'review_email_scheduled_for']

admin.site.register(AffiliateLink, AffiliateAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Affiliate)
admin.site.register(App)
admin.site.register(Cart)
admin.site.register(CartItem)

admin.site.register(AffiliatePartner)
admin.site.register(AffiliateTransaction)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderStatusLog, OrderStatusLogAdmin)
admin.site.register(OrderItem)
admin.site.register(AffiliateCode)
admin.site.register(DiscountCode)
admin.site.register(WalletCode)
admin.site.register(Wallet)
admin.site.register(SaleBadge)
admin.site.register(AppGroup)
admin.site.register(Voucher)
admin.site.register(VoucherOrder)
from .models import AppReview

@admin.register(AppReview)
class AppReviewAdmin(admin.ModelAdmin):
    list_display = ('app', 'user', 'stars', 'comment', 'is_approved', 'created_at')
    list_filter = ('stars', 'is_approved', 'app')
    list_editable = ('is_approved',)
    search_fields = ('user__username', 'app__name', 'comment')
    ordering = ('-created_at',)

