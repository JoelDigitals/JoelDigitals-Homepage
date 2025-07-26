from django.contrib import admin
from .models import App, AppStatus, AppIssue, GlobalIssue

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ['name', 'server_url', 'is_active']

@admin.register(AppStatus)
class AppStatusAdmin(admin.ModelAdmin):
    list_display = ['app', 'status', 'response_time_ms', 'timestamp']

@admin.register(AppIssue)
class AppIssueAdmin(admin.ModelAdmin):
    list_display = ['app', 'title', 'is_resolved', 'created']
    list_filter = ['is_resolved']

@admin.register(GlobalIssue)
class GlobalIssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_resolved', 'created']
    list_filter = ['is_resolved']
