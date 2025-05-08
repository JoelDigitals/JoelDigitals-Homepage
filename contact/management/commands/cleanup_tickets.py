from django.core.management.base import BaseCommand
from contact.models import SupportTicket
from django.utils.timezone import now
from datetime import timedelta

class Command(BaseCommand):
    help = 'Deletes resolved tickets older than 3 days'

    def handle(self, *args, **kwargs):
        cutoff = now() - timedelta(days=3)
        old_tickets = SupportTicket.objects.filter(is_resolved=True, created_at__lt=cutoff)
        count = old_tickets.count()
        old_tickets.delete()
        self.stdout.write(f"Deleted {count} resolved tickets older than 3 days.")
