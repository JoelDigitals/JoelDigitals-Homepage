from django.contrib import admin
from .models import App, OperatingSystem, Download, DownloadPackage, DownloadPackageApp, AccessCode, CodeRedemption, DownloadSession, AccessSuspension


class DownloadInline(admin.TabularInline):
    model = Download
    extra = 0
    fields = ('operating_system', 'version', 'external_link', 'file_url', 'release_date')


class AppInline(admin.TabularInline):
    model = Download
    extra = 0
    fields = ('operating_system', 'version', 'external_link', 'file_url')
    verbose_name = "Download Link"
    verbose_name_plural = "Download Links"


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [AppInline]


class PackageAppInline(admin.TabularInline):
    model = DownloadPackageApp
    extra = 1
    fields = ('app', 'os', 'download_link', 'download', 'order')
    autocomplete_fields = ['app']
    verbose_name = "App im Paket"
    verbose_name_plural = "Apps im Paket"


@admin.register(DownloadPackage)
class DownloadPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'created_at')
    list_editable = ('is_active',)
    inlines = [PackageAppInline]


@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'package', 'used_count', 'max_uses', 'is_active', 'expires_at')
    list_filter = ('package', 'is_active')
    search_fields = ('code',)
    readonly_fields = ('used_count',)


@admin.register(OperatingSystem)
class OperatingSystemAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('app', 'operating_system', 'version', 'release_date')
    list_filter = ('app', 'operating_system')


@admin.register(CodeRedemption)
class CodeRedemptionAdmin(admin.ModelAdmin):
    list_display = ('code', 'ip_address', 'redeemed_at')
    list_filter = ('code__package',)
    readonly_fields = ('code', 'ip_address', 'user_agent', 'device_info', 'redeemed_at')


@admin.register(DownloadSession)
class DownloadSessionAdmin(admin.ModelAdmin):
    list_display = ('package_app', 'ip_address', 'downloaded_at')
    readonly_fields = ('redemption', 'package_app', 'ip_address', 'user_agent', 'downloaded_at')


@admin.register(AccessSuspension)
class AccessSuspensionAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reason', 'is_active', 'suspended_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
