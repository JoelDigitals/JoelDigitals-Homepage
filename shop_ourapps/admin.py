from django.contrib import admin
from .models import (
    Purchase, AffiliateLink, Affiliate, App, Cart, CartItem, AffiliateTransaction, 
    AffiliatePartner, Order, OrderItem, AffiliateCode, DiscountCode, Wallet, WalletCode, 
    AppGroup, Voucher, VoucherOrder, SaleBadge, OrderStatusLog,
    AffiliateMarketingMaterial, AffiliateInvoice,
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



from .models import ReturnRequest, AppReview

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display  = ('id', 'order', 'user', 'reason', 'status', 'created_at')
    list_filter   = ('status', 'reason')
    list_editable = ('status',)
    search_fields = ('user__username', 'order__id', 'description')
    ordering      = ('-created_at',)


@admin.register(AffiliateMarketingMaterial)
class AffiliateMarketingMaterialAdmin(admin.ModelAdmin):
    list_display = ('title_de', 'title_en', 'created_at')
    search_fields = ('title_de', 'title_en')


@admin.register(AffiliateInvoice)
class AffiliateInvoiceAdmin(admin.ModelAdmin):
    list_display = ('partner', 'amount', 'is_credited', 'created_at')
    list_filter = ('is_credited', 'partner')
    search_fields = ('partner__name', 'description')
    actions = ['credit_to_wallet']

    @admin.action(description="Betrag dem Affiliate-Wallet gutschreiben")
    def credit_to_wallet(self, request, queryset):
        from django.db.models import F
        from decimal import Decimal
        from django.utils import timezone
        count = 0
        for inv in queryset.filter(is_credited=False):
            wallet, _ = Wallet.objects.get_or_create(user=inv.partner.user)
            Wallet.objects.filter(id=wallet.id).update(
                pending_earnings=F('pending_earnings') + inv.amount
            )
            inv.is_credited = True
            inv.credited_at = timezone.now()
            inv.save(update_fields=['is_credited', 'credited_at'])
            count += 1
        self.message_user(request, f"{count} Rechnung(en) gutgeschrieben.")
