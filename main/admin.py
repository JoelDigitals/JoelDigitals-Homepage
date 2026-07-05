from django.contrib import admin
from .models import TeamMember, OpeningHour, SpecialOpeningHour, SSOClient_Authorization, SSOClient, SSOSession, FAQ, SSOAuthorization, SSOScope, UserProfile, Newsletter
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "marketing_opt_in", "marketing_token", "phone", "created_at")
    list_filter = ("marketing_opt_in",)
    search_fields = ("user__username", "user__email", "phone", "company")
    readonly_fields = ("marketing_token", "created_at", "updated_at")
    list_select_related = ("user",)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "created_by", "status", "recipient_count", "created_at", "sent_at")
    list_filter = ("status",)
    search_fields = ("title", "subject")
    readonly_fields = ("recipient_count", "sent_at", "created_at", "updated_at")
    fieldsets = (
        ("Newsletter", {
            "fields": ("title", "subject", "subtitle", "content", "created_by")
        }),
        ("Status", {
            "fields": ("status", "recipient_count", "sent_at", "created_at", "updated_at")
        }),
    )