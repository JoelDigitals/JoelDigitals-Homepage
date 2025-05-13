from django.contrib import admin
from .models import Purchase, AffiliateLink, Affiliate, App, Cart, CartItem

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
