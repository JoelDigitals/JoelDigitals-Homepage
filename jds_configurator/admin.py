from django.contrib import admin
from .models import JdsModule, JdsConfigRequest


@admin.register(JdsModule)
class JdsModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'category', 'is_core', 'monthly_price', 'is_active')
    list_filter = ('category', 'is_core', 'is_active')
    search_fields = ('name', 'key')


@admin.register(JdsConfigRequest)
class JdsConfigRequestAdmin(admin.ModelAdmin):
    list_display = ('reference', 'status', 'first_name', 'last_name', 'email', 'company_name', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('reference', 'first_name', 'last_name', 'email', 'company_name')
    readonly_fields = ('reference', 'created_at', 'updated_at')
    filter_horizontal = ('modules',)
