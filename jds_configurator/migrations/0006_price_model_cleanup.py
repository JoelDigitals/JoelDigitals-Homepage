from django.db import migrations, models


class Migration(migrations.Migration):
    """JDS Management ist ein einmaliger Kauf (kein Abo) und Rabattcodes werden
    erst im Shop-Checkout angegeben, nicht mehr im Konfigurator selbst - daher
    entfällt die eigene Rabatt-/Zwischensumme-Verrechnung hier."""

    dependencies = [
        ('jds_configurator', '0005_jdsfeaturerequest'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jdsmodule',
            old_name='monthly_price',
            new_name='price',
        ),
        migrations.AlterField(
            model_name='jdsmodule',
            name='price',
            field=models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Einmaliger Preis (kein Abo)'),
        ),
        migrations.RemoveField(
            model_name='jdsconfigrequest',
            name='discount_code',
        ),
        migrations.RemoveField(
            model_name='jdsconfigrequest',
            name='discount_amount',
        ),
        migrations.RemoveField(
            model_name='jdsconfigrequest',
            name='subtotal',
        ),
        migrations.RemoveField(
            model_name='jdsconfiguration',
            name='discount_code',
        ),
        migrations.RemoveField(
            model_name='jdsconfiguration',
            name='discount_amount',
        ),
        migrations.RemoveField(
            model_name='jdsconfiguration',
            name='subtotal',
        ),
    ]
