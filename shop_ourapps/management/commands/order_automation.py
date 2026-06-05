"""
Management Command für Shop-Automatisierung.

Verwendung:
    python manage.py order_automation
    python manage.py order_automation --deliver
    python manage.py order_automation --reviews
"""
from django.core.management.base import BaseCommand
from shop_ourapps.services.automation_service import OrderAutomationService


class Command(BaseCommand):
    help = 'Führt automatische Order-Verarbeitungstasks aus'

    def add_arguments(self, parser):
        parser.add_argument(
            '--deliver',
            action='store_true',
            help='Markiere ausstehende Bestellungen als geliefert (nach 30 Min)',
        )
        parser.add_argument(
            '--reviews',
            action='store_true',
            help='Versende ausstehende Review-Emails',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Führe alle Tasks aus',
        )

    def handle(self, *args, **options):
        if not any([options['deliver'], options['reviews'], options['all']]):
            options['all'] = True

        if options['deliver'] or options['all']:
            self.stdout.write(self.style.WARNING('📦 Starten von Auto-Delivery...'))
            count = OrderAutomationService.auto_deliver_after_30_minutes()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {count} Bestellung(en) als geliefert markiert')
            )

        if options['reviews'] or options['all']:
            self.stdout.write(self.style.WARNING('📧 Starten von Review-Email Versand...'))
            count = OrderAutomationService.send_review_emails()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {count} Review-Email(s) versendet')
            )

        # Status anzeigen
        stats = OrderAutomationService.get_pending_orders_stats()
        self.stdout.write(self.style.SUCCESS('\n📊 Status:'))
        self.stdout.write(f'  Ausstehende Lieferungen: {stats["pending_delivery"]}')
        self.stdout.write(f'  Ausstehende Review-Emails: {stats["pending_review"]}')
