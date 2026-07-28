from django.db import migrations

REMOVED_TECHS = ['squarespace', 'webflow', 'typo3', 'joomla']


def cleanup(apps, schema_editor):
    BasePricingOption = apps.get_model('website_configurator', 'BasePricingOption')
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')

    BasePricingOption.objects.filter(tech__in=REMOVED_TECHS).delete()

    for f in ConfiguratorFeature.objects.all():
        parts = [t.strip() for t in f.techs.split(',') if t.strip() and t.strip() not in REMOVED_TECHS]
        joined = ','.join(parts)
        if joined != f.techs:
            f.techs = joined
            f.save(update_fields=['techs'])


def noop_reverse(apps, schema_editor):
    # Nicht rueckwaerts rekonstruierbar (welche Features vorher welche Techs
    # hatten, ist nicht mehr bekannt) - bewusst ohne Reverse-Datenwiederherstellung.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0011_alter_basepricingoption_tech_and_more'),
    ]

    operations = [
        migrations.RunPython(cleanup, noop_reverse),
    ]
