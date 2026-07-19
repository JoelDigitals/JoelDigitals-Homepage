from decimal import Decimal
from django.db import migrations

# Angepasste Preise der Zusatzmodule, sodass Basismodul (59,99 €) + alle
# Zusatzmodule zusammen ca. 250 €/Monat ergeben (siehe jds_configurator/models.py
# JdsConfigRequest.BASISMODUL_PRICE). Bewertung nach Komplexitaet/Funktionsumfang
# des jeweiligen Moduls.
NEW_PRICES = {
    'jobs': Decimal('29.99'),
    'it': Decimal('25.99'),
    'leads': Decimal('20.99'),
    'tasks': Decimal('16.99'),
    'meetings': Decimal('14.99'),
    'production': Decimal('13.99'),
    'visitors': Decimal('12.49'),
    'qualifications': Decimal('11.49'),
    'inventory': Decimal('9.99'),
    'fahrten': Decimal('8.99'),
    'statistics': Decimal('7.99'),
    'deliveries': Decimal('6.49'),
    'subteam': Decimal('5.49'),
    'tax': Decimal('3.49'),
}

OLD_PRICES = {
    'fahrten': Decimal('5.00'),
    'leads': Decimal('9.49'),
    'subteam': Decimal('2.00'),
    'tasks': Decimal('9.99'),
    'visitors': Decimal('5.50'),
    'jobs': Decimal('19.99'),
    'qualifications': Decimal('2.00'),
    'inventory': Decimal('5.00'),
    'deliveries': Decimal('2.00'),
    'production': Decimal('4.99'),
    'tax': Decimal('0.99'),
    'statistics': Decimal('1.99'),
    'it': Decimal('15.00'),
    'meetings': Decimal('10.00'),
}


def apply_prices(apps, schema_editor, prices):
    JdsModule = apps.get_model('jds_configurator', 'JdsModule')
    for key, price in prices.items():
        JdsModule.objects.filter(key=key).update(monthly_price=price)


def forwards(apps, schema_editor):
    apply_prices(apps, schema_editor, NEW_PRICES)


def backwards(apps, schema_editor):
    apply_prices(apps, schema_editor, OLD_PRICES)


class Migration(migrations.Migration):

    dependencies = [
        ('jds_configurator', '0002_seed_modules'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
