from django.contrib import admin
from .models import BackroomProduct, BackroomAccessRequest

@admin.register(BackroomProduct)
class BackroomProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'uvp', 'discount_percent', 'requires_activation', 'is_published', 'order', 'created_at')
    list_filter = ('is_published', 'requires_activation')
    search_fields = ('name', 'name_english', 'description', 'description_english')
    list_editable = ('order', 'is_published')
    prepopulated_fields = {"slug": ("name",)}
    fields = (
        'name', 'name_english', 'slug', 'description', 'description_english', 'image',
        'price', 'uvp',
        'discount_percent', 'discount_start', 'discount_end',
        'requires_activation', 'is_published', 'order',
    )


@admin.register(BackroomAccessRequest)
class BackroomAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'processed_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'message')
    readonly_fields = ('user', 'message', 'created_at')

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for req in queryset.exclude(status='approved'):
            req.approve()
    approve_requests.short_description = "Ausgewählte Anfragen genehmigen (+ Gruppe zuweisen)"

    def reject_requests(self, request, queryset):
        for req in queryset.exclude(status='rejected'):
            req.reject()
    reject_requests.short_description = "Ausgewählte Anfragen ablehnen"
