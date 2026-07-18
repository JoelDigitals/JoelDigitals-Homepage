from django.contrib import admin

from .models import CallbackRequest, PushHealthCheck, StatusSubscription


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'phone', 'created_at', 'handled']
    list_filter = ['handled']
    list_editable = ['handled']
    search_fields = ['order__id', 'user__username', 'phone']


@admin.register(PushHealthCheck)
class PushHealthCheckAdmin(admin.ModelAdmin):
    list_display = ['checked_at', 'success', 'detail']
    list_filter = ['success']
    readonly_fields = ['checked_at', 'success', 'detail']


@admin.register(StatusSubscription)
class StatusSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'app', 'created_at']
    list_filter = ['app']
    search_fields = ['user__username', 'app__name']
