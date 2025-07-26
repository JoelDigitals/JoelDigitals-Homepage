from django.contrib import admin
from .models import App, OperatingSystem, Download

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(OperatingSystem)
class OperatingSystemAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('app', 'operating_system', 'version', 'release_date')
    list_filter = ('app', 'operating_system')
