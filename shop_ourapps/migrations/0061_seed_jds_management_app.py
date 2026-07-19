from decimal import Decimal
from django.db import migrations

JDS_SLUG = 'jds-management-individuell'


def seed_app(apps, schema_editor):
    App = apps.get_model('shop_ourapps', 'App')
    App.objects.get_or_create(
        slug=JDS_SLUG,
        defaults={
            'name': 'JDS Management',
            'description': (
                "Dein individuelles JDS Management: Team, Arbeitszeiten, Rollenverwaltung, "
                "Rechnungen, Finanzen, Lager, Angebote, Produkte, Kunden, Chat und Kalender im "
                "Basismodul enthalten, dazu 6 User. Zusatzmodule und weitere User buchst du im "
                "Konfigurator dazu."
            ),
            'version': '1.0',
            'is_available_for_purchase': True,
            'is_active': True,
            'price': Decimal('59.99'),
            'requires_shipping': False,
            'is_physical': False,
        },
    )


def unseed_app(apps, schema_editor):
    App = apps.get_model('shop_ourapps', 'App')
    App.objects.filter(slug=JDS_SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shop_ourapps', '0060_cartitem_jds_configuration_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_app, unseed_app),
    ]
