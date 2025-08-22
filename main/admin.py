from django.contrib import admin
from .models import TeamMember, OpeningHour, SpecialOpeningHour

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
