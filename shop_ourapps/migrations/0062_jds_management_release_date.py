from datetime import date
from django.db import migrations

JDS_SLUG = 'jds-management-individuell'
RELEASE_DATE = date(2026, 7, 21)


def set_release_date(apps, schema_editor):
    App = apps.get_model('shop_ourapps', 'App')
    App.objects.filter(slug=JDS_SLUG).update(release_date=RELEASE_DATE)


def unset_release_date(apps, schema_editor):
    App = apps.get_model('shop_ourapps', 'App')
    App.objects.filter(slug=JDS_SLUG).update(release_date=None)


class Migration(migrations.Migration):

    dependencies = [
        ('shop_ourapps', '0061_seed_jds_management_app'),
    ]

    operations = [
        migrations.RunPython(set_release_date, unset_release_date),
    ]
