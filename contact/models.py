from django.db import models
from django.contrib.auth.models import User
import uuid
from shop_ourapps.models import App

class SalesEntry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class SalesWish(models.Model):
    entry = models.ForeignKey(SalesEntry, on_delete=models.CASCADE, related_name='wishes')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}"


from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now

class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    PLATFORM_CHOICES = [
        ('web', 'Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tickets')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    ticket_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    app_name = models.ForeignKey(App, on_delete=models.CASCADE, null=True, blank=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='web')
    is_archived = models.BooleanField(default=False)

    def check_auto_archive(self):
        if self.is_resolved and self.resolved_at:
            delta = now() - self.resolved_at
            if delta > timedelta(hours=48):
                self.is_archived = True
                self.save()

    def reactivate_if_new_message(self, user):
        if self.is_archived and user == self.user:
            self.is_archived = False
            self.is_resolved = False
            self.resolved_at = None
            self.save()

    def priority_value(self):
        return {'hoch': 3, 'normal': 2, 'niedrig': 1}.get(self.priority, 0)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            while True:
                new_ticket_number = f"T-{uuid.uuid4().hex[:10].upper()}"
                if not SupportTicket.objects.filter(ticket_number=new_ticket_number).exists():
                    self.ticket_number = new_ticket_number
                    break
        super().save(*args, **kwargs)

    def should_archive(self):
        return self.is_resolved and (timezone.now() - self.created_at > timedelta(hours=24))

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.subject}"

class TicketNote(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note by {self.author} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey('SupportTicket', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nachricht von {self.sender} am {self.created_at}"
    
class SalesChatMessage(models.Model):
    entry = models.ForeignKey(SalesEntry, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"

class AppointmentType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('accepted', 'Angenommen'),
        ('rejected', 'Abgelehnt'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    appointment_type = models.ForeignKey('AppointmentType', on_delete=models.SET_NULL, null=True)
    appointment_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} – {self.appointment_datetime.strftime('%d.%m.%Y %H:%M')}"