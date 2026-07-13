from django.contrib import admin

from .models import CallbackRequest


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'phone', 'created_at', 'handled']
    list_filter = ['handled']
    list_editable = ['handled']
    search_fields = ['order__id', 'user__username', 'phone']
