from django.core.management.base import BaseCommand
from shop_ourapps.services.jds_api import sync_stock


class Command(BaseCommand):
    help = "Sync stock levels from JDS Management API"

    def handle(self, *args, **options):
        updated = sync_stock()
        if updated:
            self.stdout.write(self.style.SUCCESS(f"Stock updated for {updated} products"))
        else:
            self.stdout.write(self.style.WARNING("No products updated"))
