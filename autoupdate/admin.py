from django.contrib import admin
from .models import AutoUpdateApp, AutoUpdateVersion


class VersionInline(admin.TabularInline):
    model = AutoUpdateVersion
    extra = 1
    fields = ('version', 'release_date', 'download_link', 'is_active')


@admin.register(AutoUpdateApp)
class AutoUpdateAppAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'latest_version', 'version_count')
    search_fields = ('name',)
    inlines = [VersionInline]

    def latest_version(self, obj):
        latest = obj.versions.filter(is_active=True).first()
        return latest.version if latest else "-"
    latest_version.short_description = "Letzte Version"

    def version_count(self, obj):
        return obj.versions.count()
    version_count.short_description = "Versionen"


@admin.register(AutoUpdateVersion)
class AutoUpdateVersionAdmin(admin.ModelAdmin):
    list_display = ('app', 'version', 'release_date', 'is_active')
    list_filter = ('app', 'is_active')
    search_fields = ('app__name', 'version')
