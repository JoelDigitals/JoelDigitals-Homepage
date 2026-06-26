from django.contrib import admin
from .models import Webinar, WebinarRegistration


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_time', 'duration_minutes', 'max_participants', 'spots_remaining', 'is_active']
    list_filter = ['is_active', 'date_time']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'title_en', 'slug', 'description', 'description_en', 'image')
        }),
        ('Termin', {
            'fields': ('date_time', 'duration_minutes', 'max_participants')
        }),
        ('Anmeldung', {
            'fields': ('registration_start', 'registration_end')
        }),
        ('Links', {
            'fields': ('meeting_url', 'recording_url')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    actions = ['send_reminders_to_all']

    @admin.action(description="🔔 Erinnerungsmail an ALLE registrierten Teilnehmer senden")
    def send_reminders_to_all(self, request, queryset):
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from .models import WebinarRegistration
        total = 0
        errors = 0
        for webinar in queryset:
            registrations = WebinarRegistration.objects.filter(webinar=webinar, status='registered', reminder_sent=False)
            for reg in registrations:
                try:
                    ctx = {'user': reg.user, 'webinar': reg.webinar}
                    html = render_to_string('emails/webinar_reminder.html', ctx)
                    msg = EmailMultiAlternatives(
                        subject=f"🔔 Erinnerung: {webinar.title} beginnt bald!",
                        body="",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[reg.user.email],
                    )
                    msg.attach_alternative(html, "text/html")
                    msg.send()
                    reg.reminder_sent = True
                    reg.save(update_fields=['reminder_sent'])
                    total += 1
                except Exception:
                    errors += 1
        msg = f"{total} Erinnerung(en) gesendet."
        if errors:
            msg += f" {errors} Fehler."
        self.message_user(request, msg)


@admin.register(WebinarRegistration)
class WebinarRegistrationAdmin(admin.ModelAdmin):
    list_display = ['webinar', 'user', 'status', 'registered_at', 'reminder_sent']
    list_filter = ['status', 'webinar', 'reminder_sent']
    search_fields = ['user__username', 'user__email', 'webinar__title']
    readonly_fields = ['registered_at']
    actions = ['mark_attended', 'mark_no_show', 'send_reminder']

    @admin.action(description="Als 'Teilgenommen' markieren")
    def mark_attended(self, request, queryset):
        updated = queryset.update(status='attended')
        self.message_user(request, f"{updated} Anmeldung(en) als 'Teilgenommen' markiert.")

    @admin.action(description="Als 'Nicht erschienen' markieren")
    def mark_no_show(self, request, queryset):
        updated = queryset.update(status='no_show')
        self.message_user(request, f"{updated} Anmeldung(en) als 'Nicht erschienen' markiert.")

    @admin.action(description="🔔 Erinnerungsmail mit Beitrittslink senden")
    def send_reminder(self, request, queryset):
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        sent = 0
        errors = 0
        for reg in queryset.filter(status='registered'):
            try:
                ctx = {'user': reg.user, 'webinar': reg.webinar}
                html = render_to_string('emails/webinar_reminder.html', ctx)
                msg = EmailMultiAlternatives(
                    subject=f"🔔 Erinnerung: {reg.webinar.title} beginnt bald!",
                    body="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[reg.user.email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send()
                reg.reminder_sent = True
                reg.save(update_fields=['reminder_sent'])
                sent += 1
            except Exception:
                errors += 1
        msg = f"{sent} Erinnerung(en) gesendet."
        if errors:
            msg += f" {errors} Fehler."
        self.message_user(request, msg)
