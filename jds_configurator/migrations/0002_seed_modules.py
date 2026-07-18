from decimal import Decimal
from django.db import migrations

# Basismodul (Pflicht, im Fixpreis von 59,99€ enthalten - siehe JdsConfigRequest.BASISMODUL_PRICE)
CORE_MODULES = [
    ('team_page', 'Team Page', 'basis', 0),
    ('worktime', 'Arbeitszeiten/Schichten', 'basis', 1),
    ('vacation', 'Urlaub/Krankmeldungen', 'basis', 2),
    ('roles', 'Rollenverwaltung', 'basis', 3),
    ('invoices', 'Rechnungen', 'basis', 4),
    ('finance', 'Einnahmen/Ausgaben und Konten', 'basis', 5),
    ('invite_user', 'User einladen', 'basis', 6),
    ('storage', 'Lager', 'basis', 7),
    ('quotes', 'Angebote', 'basis', 8),
    ('products', 'Produkte', 'basis', 9),
    ('customers', 'Kunden', 'basis', 10),
    ('chat', 'Chat', 'basis', 11),
    ('calendar', 'Kalender', 'basis', 12),
]

# (key, name, category, preis, sort_order)
ADDON_MODULES = [
    ('fahrten', 'Fahrtkosten/Fahrzeugverwaltung', 'fuhrpark', Decimal('5.00'), 0),
    ('leads', 'Leadmanagement', 'verkauf', Decimal('9.49'), 0),
    ('subteam', 'Oberteam', 'organisation', Decimal('2.00'), 0),
    ('tasks', 'Aufgabenverwaltung', 'organisation', Decimal('9.99'), 1),
    ('visitors', 'Besuchermanagement', 'organisation', Decimal('5.50'), 2),
    ('jobs', 'Bewerbungssystem', 'personal', Decimal('19.99'), 0),
    ('qualifications', 'Qualifikationen & Zertifikate', 'personal', Decimal('2.00'), 1),
    ('inventory', 'Inventur', 'produktion', Decimal('5.00'), 0),
    ('deliveries', 'Lieferungen', 'produktion', Decimal('2.00'), 1),
    ('production', 'Produktion von Produkten', 'produktion', Decimal('4.99'), 2),
    ('tax', 'Steuerberechnung', 'verkauf', Decimal('0.99'), 1),
    ('statistics', 'Statistiken', 'verkauf', Decimal('1.99'), 2),
    ('it', 'IT-Modul', 'it', Decimal('15.00'), 0),
    ('meetings', 'Meetings und Räume', 'organisation', Decimal('10.00'), 3),
]


def seed_modules(apps, schema_editor):
    JdsModule = apps.get_model('jds_configurator', 'JdsModule')
    for key, name, category, sort_order in CORE_MODULES:
        JdsModule.objects.get_or_create(
            key=key, defaults={'name': name, 'category': category, 'is_core': True,
                                'monthly_price': Decimal('0.00'), 'sort_order': sort_order}
        )
    for key, name, category, price, sort_order in ADDON_MODULES:
        JdsModule.objects.get_or_create(
            key=key, defaults={'name': name, 'category': category, 'is_core': False,
                                'monthly_price': price, 'sort_order': sort_order}
        )


def unseed_modules(apps, schema_editor):
    JdsModule = apps.get_model('jds_configurator', 'JdsModule')
    all_keys = [k for k, *_ in CORE_MODULES] + [k for k, *_ in ADDON_MODULES]
    JdsModule.objects.filter(key__in=all_keys).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('jds_configurator', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_modules, unseed_modules),
    ]
