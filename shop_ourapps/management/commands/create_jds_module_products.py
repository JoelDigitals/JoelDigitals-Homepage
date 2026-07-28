from django.core.management.base import BaseCommand

from jds_configurator.models import JdsModule
from shop_ourapps.services import jds_api


class Command(BaseCommand):
    """Legt fuer jedes JdsModule (Kern- und Zusatzmodule von 'Dein individuelles
    JDS Management') ein Produkt im echten JDS Management an, ueber die
    bestehende jds_api-Integration (Team wird durch settings.JDS_TEAM_CODE/
    JDS_API_TOKEN bestimmt, siehe .env). Kein Dedup serverseitig - dieser
    Befehl ist fuer einen einmaligen Bulk-Import gedacht, nicht fuer
    wiederholten Aufruf (siehe --dry-run zum Pruefen vor dem echten Anlegen)."""

    help = "Legt alle JdsModule (Kern- + Zusatzmodule) als Produkte im echten JDS Management an."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, was angelegt wuerde - keine echten API-Aufrufe.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        modules = JdsModule.objects.filter(is_active=True).order_by('-is_core', 'category', 'sort_order', 'name')

        created, failed = 0, 0
        for m in modules:
            payload = {
                'name': f"JDS Management: {m.name}",
                'price': str(m.price),
                'mwst': '0',  # Kleinunternehmer nach § 19 Abs. 1 UStG - keine Umsatzsteuer
                'description': m.description or ('Bestandteil des Basismoduls' if m.is_core else 'Zusatzmodul'),
                'product_number': f"JDSMOD-{m.key.upper()}",
            }

            if dry_run:
                self.stdout.write(f"[DRY RUN] {payload['product_number']:<20} {payload['name']:<50} {payload['price']:>8} EUR")
                continue

            try:
                result = jds_api.create_product(payload)
                self.stdout.write(self.style.SUCCESS(
                    f"Angelegt: {payload['product_number']} - {m.name} (Produkt-ID {result.get('id')})"
                ))
                created += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fehler bei {m.name} ({payload['product_number']}): {e}"))
                failed += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\nDry-Run: {modules.count()} Produkte wuerden angelegt (kein API-Aufruf erfolgt)."))
        else:
            self.stdout.write(f"\nFertig: {created} angelegt, {failed} Fehler.")
