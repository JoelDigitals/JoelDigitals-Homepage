from django.db import migrations

# Feature-Site-Type-Korrekturen: einige Features waren fuer 'shop' (oder
# 'onepager') gelistet, obwohl sie inhaltlich nicht dazu passen (z.B.
# Karriere-Seite bei einem reinen Online-Shop, Presseseite auf einer
# Ein-Seiten-Website). site_types je Feature-Key -> neue, korrekte Liste.
FEATURE_SITE_TYPE_FIXES = {
    'portfolio': 'onepager,multipage',       # Referenzen-Galerie passt nicht zum Shop-Checkout-Flow
    'jobs': 'multipage',                     # Karriere-Seite braucht eine echte Mehrseiten-Struktur
    'press': 'multipage',                    # Presse/News-Bereich ist ein Mehrseiten-Feature
    'photography': 'multipage,shop',         # Produktfotografie passt nicht zum minimalen Onepager
}


def apply_fixes(apps, schema_editor):
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    for key, site_types in FEATURE_SITE_TYPE_FIXES.items():
        ConfiguratorFeature.objects.filter(key=key).update(site_types=site_types)


def revert_fixes(apps, schema_editor):
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    ConfiguratorFeature.objects.filter(key__in=FEATURE_SITE_TYPE_FIXES.keys()).update(site_types='onepager,multipage,shop')


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0005_websiteconfigrequest_terms_accepted_and_more'),
    ]

    operations = [
        migrations.RunPython(apply_fixes, revert_fixes),
    ]
