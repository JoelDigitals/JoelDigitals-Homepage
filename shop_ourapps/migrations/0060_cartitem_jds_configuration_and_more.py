import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_ourapps', '0059_order_voucher_order_voucher_amount_and_more'),
        ('jds_configurator', '0004_jdsconfiguration_extra_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='jds_configuration',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                to='jds_configurator.jdsconfiguration',
                help_text='Individuelle JDS-Management-Konfiguration (Module + User) statt eines Katalog-Preises',
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='jds_configuration',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                to='jds_configurator.jdsconfiguration',
                help_text='Individuelle JDS-Management-Konfiguration (Module + User) statt eines Katalog-Preises',
            ),
        ),
    ]
