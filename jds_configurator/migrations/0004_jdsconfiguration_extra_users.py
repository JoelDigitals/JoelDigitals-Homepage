from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jds_configurator', '0003_module_price_update'),
        ('shop_ourapps', '0059_order_voucher_order_voucher_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jdsconfigrequest',
            name='extra_users',
            field=models.PositiveIntegerField(default=0, help_text='Zusätzliche User über die im Basismodul enthaltenen 6 hinaus'),
        ),
        migrations.CreateModel(
            name='JdsConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extra_users', models.PositiveIntegerField(default=0)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('discount_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop_ourapps.discountcode')),
                ('modules', models.ManyToManyField(blank=True, related_name='cart_configurations', to='jds_configurator.jdsmodule')),
            ],
        ),
    ]
