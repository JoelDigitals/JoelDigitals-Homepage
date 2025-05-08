from django.db import models
from django.contrib.auth.models import User
import uuid

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


class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    ticket_number = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generiere eine sichere eindeutige Ticketnummer
            while True:
                new_ticket_number = f"T-{uuid.uuid4().hex[:10].upper()}"
                if not SupportTicket.objects.filter(ticket_number=new_ticket_number).exists():
                    self.ticket_number = new_ticket_number
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.subject}"

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
