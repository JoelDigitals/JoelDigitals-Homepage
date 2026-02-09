from django.contrib import admin
from .models import TeamMember, OpeningHour, SpecialOpeningHour, SSOClient_Authorization, SSOClient, SSOSession, FAQ, SSOAuthorization, SSOScope
from django.contrib import admin
from django.utils.html import format_html

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question_de", "question_en", "is_published", "order", "created_at")
    list_filter = ("is_published",)
    search_fields = (
        "question_de", "question_en",
        "short_answer_de", "short_answer_en",
        "answer_de", "answer_en",
    )
    prepopulated_fields = {"slug": ("question_en",)}
    ordering = ("order",)

    fieldsets = (
        ("Deutsch", {
            "fields": ("question_de", "short_answer_de", "answer_de", "detail_content_de")
        }),
        ("English", {
            "fields": ("question_en", "short_answer_en", "answer_en", "detail_content_en")
        }),
        ("Allgemein", {
            "fields": ("slug", "is_published", "order", "created_at", "updated_at")
        }),
    )

    readonly_fields = ("created_at", "updated_at")

# Register your models here.

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'position')

@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ("weekday", "open_time", "close_time", "closed")
    ordering = ("weekday",)

@admin.register(SpecialOpeningHour)
class SpecialOpeningHourAdmin(admin.ModelAdmin):
    list_display = ("date", "open_time", "close_time", "closed", "note")
    ordering = ("date",)

admin.site.register(SSOClient)
admin.site.register(SSOSession)
admin.site.register(SSOAuthorization)
admin.site.register(SSOScope)
admin.site.register(SSOClient_Authorization)