from decimal import Decimal
from django.db import migrations

# (site_type, tech, base_price, included_pages, extra_page_price)
BASE_OPTIONS = [
    ('onepager', 'custom', Decimal('890.00'), 1, Decimal('0.00')),
    ('onepager', 'wordpress', Decimal('590.00'), 1, Decimal('0.00')),
    ('onepager', 'other', Decimal('0.00'), 1, Decimal('0.00')),
    ('multipage', 'custom', Decimal('1690.00'), 5, Decimal('60.00')),
    ('multipage', 'wordpress', Decimal('990.00'), 5, Decimal('45.00')),
    ('multipage', 'other', Decimal('0.00'), 5, Decimal('0.00')),
    ('shop', 'custom', Decimal('2990.00'), 1, Decimal('0.00')),
    ('shop', 'wordpress', Decimal('1690.00'), 1, Decimal('0.00')),
    ('shop', 'shopify', Decimal('1490.00'), 1, Decimal('0.00')),
    ('shop', 'other', Decimal('0.00'), 1, Decimal('0.00')),
]

ALL_SITE_TYPES = 'onepager,multipage,shop'
ALL_TECHS = 'custom,wordpress,shopify,other'
NON_CUSTOM_TECHS = 'wordpress,shopify,other'

# (key, name, category, price, site_types, techs, sort_order)
FEATURES = [
    ('multilingual', 'Mehrsprachigkeit (weitere Sprache)', 'marketing', Decimal('250.00'), ALL_SITE_TYPES, ALL_TECHS, 0),
    ('blog', 'Blog-Bereich', 'content', Decimal('350.00'), ALL_SITE_TYPES, ALL_TECHS, 0),
    ('seo_basic', 'SEO-Grundoptimierung', 'marketing', Decimal('200.00'), ALL_SITE_TYPES, ALL_TECHS, 1),
    ('seo_advanced', 'Erweiterte SEO (Keyword-Recherche & Content-Optimierung)', 'marketing', Decimal('450.00'), ALL_SITE_TYPES, ALL_TECHS, 2),
    ('newsletter', 'Newsletter-Anbindung', 'marketing', Decimal('150.00'), ALL_SITE_TYPES, ALL_TECHS, 3),
    ('booking', 'Terminbuchungssystem', 'technik', Decimal('350.00'), ALL_SITE_TYPES, ALL_TECHS, 0),
    ('membership', 'Mitgliederbereich / Kundenlogin', 'technik', Decimal('550.00'), ALL_SITE_TYPES, ALL_TECHS, 1),
    ('cms_training', 'Einweisung/Schulung in die Pflege', 'technik', Decimal('150.00'), ALL_SITE_TYPES, NON_CUSTOM_TECHS, 2),
    ('custom_design', 'Individuelles Design statt Standard-Template', 'design', Decimal('450.00'), ALL_SITE_TYPES, NON_CUSTOM_TECHS, 0),
    ('product_filter', 'Produktvarianten & erweiterte Filter', 'shop', Decimal('300.00'), 'shop', ALL_TECHS, 0),
    ('payment_extra', 'Erweiterte Zahlungsanbindung (mehrere Anbieter)', 'shop', Decimal('200.00'), 'shop', ALL_TECHS, 1),
    ('discounts', 'Rabatt- & Gutscheinsystem', 'shop', Decimal('150.00'), 'shop', ALL_TECHS, 2),
]


def seed(apps, schema_editor):
    BasePricingOption = apps.get_model('website_configurator', 'BasePricingOption')
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')

    for site_type, tech, base_price, included_pages, extra_page_price in BASE_OPTIONS:
        BasePricingOption.objects.get_or_create(
            site_type=site_type, tech=tech,
            defaults={'base_price': base_price, 'included_pages': included_pages, 'extra_page_price': extra_page_price},
        )

    for key, name, category, price, site_types, techs, sort_order in FEATURES:
        ConfiguratorFeature.objects.get_or_create(
            key=key,
            defaults={'name': name, 'category': category, 'price': price,
                      'site_types': site_types, 'techs': techs, 'sort_order': sort_order},
        )


def unseed(apps, schema_editor):
    BasePricingOption = apps.get_model('website_configurator', 'BasePricingOption')
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    BasePricingOption.objects.filter(
        site_type__in=[o[0] for o in BASE_OPTIONS], tech__in=[o[1] for o in BASE_OPTIONS]
    ).delete()
    ConfiguratorFeature.objects.filter(key__in=[f[0] for f in FEATURES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
