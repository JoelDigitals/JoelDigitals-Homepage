from django.core.management.base import BaseCommand, CommandError

from jds_configurator.models import JdsConfigRequest, JdsModule
from website_configurator.models import BasePricingOption, ConfiguratorFeature
from shop_ourapps.services import jds_api

# JDS Management Product.product_number ist CharField(max_length=20) - jeder
# generierte Code wird dagegen geprueft, bevor er an die API geschickt wird
# (siehe create_jds_module_products.py: "JDSMOD-QUALIFICATIONS" war mit 21
# Zeichen zu lang und hat einen 500er verursacht).
MAX_PRODUCT_NUMBER_LEN = 20

SITE_TYPE_ABBR = {'onepager': 'ONE', 'multipage': 'MUL', 'shop': 'SHO'}
TECH_ABBR = {
    'custom': 'CUSTOM', 'wordpress': 'WORDPR', 'wix': 'WIX',
    'squarespace': 'SQUARE', 'webflow': 'WEBFLO', 'shopify': 'SHOPIF',
}


def _product_number(code):
    if len(code) > MAX_PRODUCT_NUMBER_LEN:
        raise CommandError(f"Produktnummer '{code}' ist {len(code)} Zeichen lang, erlaubt sind max. {MAX_PRODUCT_NUMBER_LEN}.")
    return code


class Command(BaseCommand):
    """Legt fuer ALLES, was sich in den beiden Konfiguratoren auswaehlen laesst,
    ein Produkt im echten JDS Management an (Team ueber settings.JDS_TEAM_CODE/
    JDS_API_TOKEN bestimmt):
    - Website-Konfigurator: jede Website-Typ/Umsetzung-Preis-Kombination
      (BasePricingOption, nur die mit echtem Preis - 'Preis auf Anfrage'-
      Kombinationen ohne Festpreis werden ausgelassen) + jedes Zusatzfeature
      (ConfiguratorFeature).
    - JDS Management: EIN Produkt fuer das gebuendelte Basismodul (59,99 EUR,
      deckt alle Kernmodule ab - NICHT jedes Kernmodul einzeln, das war beim
      letzten Versuch falsch) + je ein Produkt pro Zusatzmodul (JdsModule,
      is_core=False).
    Kein Dedup serverseitig - dieser Befehl ist fuer einen einmaligen
    Bulk-Import gedacht, nicht fuer wiederholten Aufruf."""

    help = "Legt Produkte fuer alle Website-Konfigurator- und JDS-Management-Optionen im echten JDS Management an."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, was angelegt wuerde - keine echten API-Aufrufe.')
        parser.add_argument('--scope', choices=['all', 'webconfig', 'jds'], default='all', help='Nur Website-Konfigurator-Produkte, nur JDS-Management-Produkte, oder beides (Standard).')

    def _rows(self, scope='all'):
        rows = []

        if scope not in ('all', 'webconfig'):
            return self._jds_rows()
        if scope == 'webconfig':
            return self._webconfig_rows()
        return self._webconfig_rows() + self._jds_rows()

    def _webconfig_rows(self):
        rows = []

        # --- Website-Konfigurator: Basispreise (nur mit echtem Preis) ---
        for opt in BasePricingOption.objects.filter(is_active=True, base_price__gt=0).order_by('site_type', 'tech'):
            site_label = dict(BasePricingOption.SITE_TYPE_CHOICES)[opt.site_type]
            tech_label = dict(BasePricingOption.TECH_CHOICES)[opt.tech]
            code = _product_number(f"WEBB-{SITE_TYPE_ABBR[opt.site_type]}-{TECH_ABBR[opt.tech]}")
            extra_note = f" (inkl. {opt.included_pages} Seiten, je weitere {opt.extra_page_price} EUR)" if opt.included_pages > 1 else ""
            rows.append({
                'name': f"Website-Konfigurator: {site_label} ({tech_label})",
                'price': str(opt.base_price),
                'description': f"Grundpreis Website-Typ '{site_label}', Umsetzung '{tech_label}'{extra_note}",
                'product_number': code,
            })

        # --- Website-Konfigurator: Zusatzfeatures ---
        for f in ConfiguratorFeature.objects.filter(is_active=True).order_by('category', 'name'):
            code = _product_number(f"WEBF-{f.key.upper()[:14]}")
            rows.append({
                'name': f"Website-Konfigurator: {f.name}",
                'price': str(f.price),
                'description': f.description or f"Website-Konfigurator Zusatzfeature ({f.get_category_display()})",
                'product_number': code,
            })

        return rows

    def _jds_rows(self):
        rows = []

        # --- JDS Management: gebuendeltes Basismodul (ein Produkt, nicht 13 einzelne) ---
        rows.append({
            'name': "JDS Management Basismodul (inkl. TeamPage, Arbeitszeiten, Urlaub, Rollenverwaltung, Rechnungen u.v.m.)",
            'price': str(JdsConfigRequest.BASISMODUL_PRICE),
            'description': "Basismodul von 'Dein individuelles JDS Management' - buendelt alle Kernfunktionen, wird nicht einzeln verkauft.",
            'product_number': _product_number("JDSMOD-BASIS"),
        })

        # --- JDS Management: Zusatzmodule ---
        for m in JdsModule.objects.filter(is_active=True, is_core=False).order_by('category', 'sort_order', 'name'):
            code = _product_number(f"JDSA-{m.key.upper()[:14]}")
            rows.append({
                'name': f"JDS Management: {m.name}",
                'price': str(m.price),
                'description': m.description or "Zusatzmodul von 'Dein individuelles JDS Management'",
                'product_number': code,
            })

        return rows

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        rows = self._rows(scope=options['scope'])

        for r in rows:
            payload = {**r, 'mwst': '0'}  # Kleinunternehmer nach § 19 Abs. 1 UStG - keine Umsatzsteuer
            if dry_run:
                self.stdout.write(f"[DRY RUN] {payload['product_number']:<20} {payload['price']:>8} EUR  {payload['name']}")
                continue
            try:
                result = jds_api.create_product(payload)
                self.stdout.write(self.style.SUCCESS(f"Angelegt: {payload['product_number']} (Produkt-ID {result.get('id')}) - {payload['name']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fehler bei {payload['product_number']}: {e}"))

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\nDry-Run: {len(rows)} Produkte wuerden angelegt (kein API-Aufruf erfolgt)."))
        else:
            self.stdout.write(f"\nFertig: {len(rows)} Produkte verarbeitet.")
