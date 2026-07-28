from django.db import migrations


def strip_magento(apps, schema_editor):
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    for f in ConfiguratorFeature.objects.filter(techs__icontains='magento'):
        parts = [t.strip() for t in f.techs.split(',') if t.strip() and t.strip() != 'magento']
        f.techs = ','.join(parts)
        f.save(update_fields=['techs'])


def restore_magento(apps, schema_editor):
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    for f in ConfiguratorFeature.objects.filter(techs__icontains='shopify').exclude(techs__icontains='magento'):
        f.techs = f.techs + ',magento'
        f.save(update_fields=['techs'])


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0009_alter_basepricingoption_tech_and_more'),
    ]

    operations = [
        migrations.RunPython(strip_magento, restore_magento),
    ]
