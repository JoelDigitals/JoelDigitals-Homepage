from django.contrib import admin
from .models import BasePricingOption, ConfiguratorFeature, EmailTemplate, WebsiteConfigRequest


@admin.register(BasePricingOption)
class BasePricingOptionAdmin(admin.ModelAdmin):
    list_display = ['site_type', 'tech', 'base_price', 'included_pages', 'extra_page_price', 'is_active']
    list_filter = ['site_type', 'tech', 'is_active']


@admin.register(ConfiguratorFeature)
class ConfiguratorFeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'site_types', 'techs', 'is_active', 'sort_order']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'key']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'subject']


@admin.register(WebsiteConfigRequest)
class WebsiteConfigRequestAdmin(admin.ModelAdmin):
    list_display = ['reference', 'name', 'site_type', 'tech', 'estimated_total', 'status', 'terms_accepted', 'created_at']
    list_filter = ['status', 'site_type', 'tech', 'terms_accepted']
    search_fields = ['reference', 'name', 'email', 'company_name']
    readonly_fields = ['reference', 'created_at', 'updated_at', 'terms_accepted_at']
    filter_horizontal = ['features']
