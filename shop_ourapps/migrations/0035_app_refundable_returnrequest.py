from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop_ourapps', '0034_appreview_order_stripe_session_id'),
    ]
    operations = [
        migrations.AddField(
            model_name='app', name='refundable',
            field=models.BooleanField(default=False, help_text='Kann diese App zurückerstattet werden?'),
        ),
        migrations.CreateModel(
            name='ReturnRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reason', models.CharField(max_length=50, choices=[
                    ('not_working','App funktioniert nicht / Startet nicht'),
                    ('technical_issue','Technisches Problem (Bug, Absturz)'),
                    ('install_failed','Installation fehlgeschlagen'),
                    ('wrong_product','Falsches Produkt erhalten'),
                    ('duplicate','Versehentlich doppelt bestellt'),
                    ('wrong_version','Falsche Version / Plattform'),
                    ('not_as_described','Entspricht nicht der Beschreibung'),
                    ('missing_feature','Erwartete Funktion fehlt'),
                    ('language_issue','Sprachproblem / Falsche Sprache'),
                    ('changed_mind','Meinung geaendert / nicht mehr benoetigt'),
                    ('price_issue','Preisproblem / guenstiger anderswo'),
                    ('other','Sonstiges'),
                ])),
                ('description', models.TextField(max_length=1000, blank=True)),
                ('status', models.CharField(max_length=20, choices=[
                    ('pending','Ausstehend - Pruefung laeuft'),
                    ('approved','Genehmigt'),
                    ('rejected','Abgelehnt'),
                    ('processing','In Bearbeitung'),
                    ('completed','Abgeschlossen - Erstattet'),
                ], default='pending')),
                ('admin_note',       models.TextField(blank=True)),
                ('tracking_number',  models.CharField(max_length=100, blank=True)),
                ('tracking_carrier', models.CharField(max_length=50, blank=True)),
                ('tracking_url',     models.URLField(blank=True)),
                ('return_label_url', models.URLField(blank=True)),
                ('refund_amount',    models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('refund_method',    models.CharField(max_length=50, blank=True)),
                ('refunded_at',      models.DateTimeField(null=True, blank=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='return_requests', to='shop_ourapps.order')),
                ('user',  models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('carrier', models.CharField(max_length=20, choices=[
                    ('DHL','DHL'),('UPS','UPS'),('DPD','DPD'),('Hermes','Hermes'),
                    ('GLS','GLS'),('FedEx','FedEx'),('PostAG','Oesterreichische Post'),
                    ('Swiss','Swiss Post'),('custom','Sonstiger Carrier'),
                ])),
                ('tracking_number',    models.CharField(max_length=100)),
                ('tracking_url',       models.URLField(blank=True)),
                ('dispatched_at',      models.DateTimeField(null=True, blank=True)),
                ('estimated_delivery', models.DateField(null=True, blank=True)),
                ('note',               models.CharField(max_length=255, blank=True)),
                ('created_at',         models.DateTimeField(auto_now_add=True)),
                ('updated_at',         models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                    related_name='shipment', to='shop_ourapps.order')),
            ],
        ),
    ]
