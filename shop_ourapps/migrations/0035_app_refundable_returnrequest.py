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
            model_name='app',
            name='refundable',
            field=models.BooleanField(
                default=False,
                help_text='Kann diese App zurückerstattet werden?'
            ),
        ),
        migrations.CreateModel(
            name='ReturnRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reason', models.CharField(max_length=50, choices=[
                    ('not_working', 'App funktioniert nicht'),
                    ('wrong_product', 'Falsches Produkt erhalten'),
                    ('duplicate', 'Versehentlich doppelt gekauft'),
                    ('not_as_described', 'Entspricht nicht der Beschreibung'),
                    ('technical_issue', 'Technisches Problem'),
                    ('other', 'Sonstiges'),
                ])),
                ('description', models.TextField(max_length=1000, blank=True)),
                ('status', models.CharField(max_length=20, choices=[
                    ('pending', 'Ausstehend'),
                    ('approved', 'Genehmigt'),
                    ('rejected', 'Abgelehnt'),
                    ('completed', 'Abgeschlossen'),
                ], default='pending')),
                ('admin_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='return_requests',
                    to='shop_ourapps.order'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
    ]
