import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jds_configurator', '0004_jdsconfiguration_extra_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JdsFeatureRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(editable=False, max_length=32, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Ausstehend'), ('in_review', 'In Prüfung'), ('approved', 'Genehmigt'), ('rejected', 'Abgelehnt')], default='pending', max_length=20)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(help_text='Gewünschte Zusatzfunktion(en) in eigenen Worten des Kunden')),
                ('internal_notes', models.TextField(blank=True, help_text='Interne Notizen / Rückfragen (nur Plattform-Admins)')),
                ('estimated_availability', models.CharField(blank=True, help_text="z.B. 'ca. 4-6 Wochen' - bei Genehmigung angeben, wird dem Kunden mitgeteilt", max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
