from django.contrib import admin
from .models import Purchase, AffiliateLink, Affiliate, App, Cart, CartItem, AffiliateTransaction, AffiliatePartner, Order, OrderItem, AffiliateCode, DiscountCode, Wallet, WalletCode, AppGroup, AffiliateCode, Voucher, VoucherOrder, SaleBadge

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'app', 'affiliate', 'date', 'full_name', 'email']
    list_filter = ['affiliate', 'app', 'date']

class AffiliateAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'commission_percent']
    search_fields = ['user__username', 'code']

admin.site.register(AffiliateLink, AffiliateAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Affiliate)
admin.site.register(App)
admin.site.register(Cart)
admin.site.register(CartItem)

admin.site.register(AffiliatePartner)
admin.site.register(AffiliateTransaction)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(AffiliateCode)
admin.site.register(DiscountCode)
admin.site.register(WalletCode)
admin.site.register(Wallet)
admin.site.register(SaleBadge)
admin.site.register(AppGroup)
admin.site.register(Voucher)
admin.site.register(VoucherOrder)