from django.contrib import admin
from django.core.mail import send_mail
from django.utils import timezone
from .models import SalesWish, SupportTicket, TicketMessage, SalesEntry, SalesChatMessage, Appointment, AppointmentType, SpecialTimeSlot, TimeSlot

admin.site.register(SalesWish)
admin.site.register(SupportTicket)
admin.site.register(TicketMessage)
admin.site.register(SalesEntry)
admin.site.register(SalesChatMessage)
admin.site.register(TimeSlot)

@admin.register(SpecialTimeSlot)
class SpecialTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'is_closed')
    list_filter = ('date', 'is_closed')

@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'appointment_type', 'appointment_datetime', 'status')
    list_filter = ('appointment_type', 'status', 'appointment_datetime')
    actions = ['mark_as_accepted', 'mark_as_rejected']

    @admin.action(description='Markiere als angenommen und sende Mail')
    def mark_as_accepted(self, request, queryset):
        for appointment in queryset:
            appointment.status = 'accepted'
            appointment.save()
            send_mail(
                subject="Termin bestätigt – Joel Digitals",
                message=(
                    f"Hallo {appointment.first_name},\n\n"
                    f"Ihr Termin am {timezone.localtime(appointment.appointment_datetime).strftime('%d.%m.%Y %H:%M')} "
                    f"wurde von Joel Digitals bestätigt.\n\nBis bald!\nIhr Joel Digitals Team"
                ),
                from_email='no-reply@joel-digitals.com',
                recipient_list=[appointment.email],
            )

    @admin.action(description='Markiere als abgelehnt und sende Mail')
    def mark_as_rejected(self, request, queryset):
        for appointment in queryset:
            appointment.status = 'rejected'
            appointment.save()
            send_mail(
                subject="Termin abgelehnt – Joel Digitals",
                message=(
                    f"Hallo {appointment.first_name},\n\n"
                    f"leider müssen wir Ihren Termin am {timezone.localtime(appointment.appointment_datetime).strftime('%d.%m.%Y %H:%M')} ablehnen.\n\n"
                    f"Bitte vereinbaren Sie einen neuen Termin oder kontaktieren Sie uns direkt.\n\n"
                    "Ihr Joel Digitals Team"
                ),
                from_email='no-reply@joel-digitals.com',
                recipient_list=[appointment.email],
            )