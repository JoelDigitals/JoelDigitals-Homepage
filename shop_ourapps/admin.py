from django.contrib import admin
from .models import (
    Purchase, AffiliateLink, Affiliate, App, Cart, CartItem, AffiliateTransaction, 
    AffiliatePartner, Order, OrderItem, AffiliateCode, DiscountCode, Wallet, WalletCode, 
    AppGroup, Voucher, VoucherOrder, SaleBadge, OrderStatusLog,
    AffiliateMarketingMaterial, AffiliateInvoice, CustomLandingPage, WithdrawalRequest,
    WatchlistEntry, Package, PackageApp,
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
class AppAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_available_for_purchase', 'release_date', 'preorder_date', 'stock']
    list_editable = ['is_active', 'is_available_for_purchase']
    list_filter = ['is_active', 'is_available_for_purchase']
    search_fields = ['name', 'slug']
    fieldsets = (
        (None, {
            'fields': ('name', 'name_english', 'slug', 'description', 'description_english', 'image')
        }),
        ('Produktdetails', {
            'fields': ('product_number', 'version', 'group')
        }),
        ('Verfügbarkeit', {
            'fields': ('is_active', 'is_available_for_purchase', 'release_date', 'preorder_date', 'stock', 'requires_shipping', 'is_physical', 'delivery_time', 'shipping_cost')
        }),
        ('Preis & Rabatt', {
            'fields': ('price', 'discount_percent', 'discount_start', 'discount_end', 'sale_badge', 'is_black_week', 'is_cyber_monday', 'is_christmas_sale')
        }),
        ('Links', {
            'fields': ('link', 'android_link', 'ios_link', 'windows_link', 'macos_link', 'linux_link')
        }),
        ('Rückgabe', {
            'fields': ('refundable', 'exchangeable')
        }),
    )


class PackageAppInline(admin.TabularInline):
    model = PackageApp
    extra = 1


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_available_for_purchase', 'is_active', 'release_date', 'preorder_date']
    list_filter = ['is_active', 'is_available_for_purchase']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PackageAppInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'name_english', 'slug', 'description', 'description_english', 'image')
        }),
        ('Verfügbarkeit', {
            'fields': ('is_active', 'is_available_for_purchase', 'release_date', 'preorder_date')
        }),
        ('Preis & Rabatt', {
            'fields': ('price', 'discount_percent', 'discount_start', 'discount_end', 'sale_badge')
        }),
    )


admin.site.register(App, AppAdmin)
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
from .models import WithdrawalRequest, AppReview

@admin.register(AppReview)
class AppReviewAdmin(admin.ModelAdmin):
    list_display = ('app', 'user', 'stars', 'comment', 'is_approved', 'created_at')
    list_filter = ('stars', 'is_approved', 'app')
    list_editable = ('is_approved',)
    search_fields = ('user__username', 'app__name', 'comment')
    ordering = ('-created_at',)



from .models import WithdrawalRequest, ReturnRequest, AppReview

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


@admin.register(CustomLandingPage)
class CustomLandingPageAdmin(admin.ModelAdmin):
    list_display = ('slug', 'greeting_name', 'headline', 'product', 'is_active')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('greeting_name',)}
    search_fields = ('slug', 'greeting_name', 'headline')


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'first_name', 'last_name', 'email', 'status', 'created_at')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('order_number', 'first_name', 'last_name', 'email')
    readonly_fields = ('created_at',)
    fieldsets = ((None, {'fields': ('order_number','first_name','last_name','email','company_name','reason')}), ('Status', {'fields': ('status','admin_note','processed_at')}))
