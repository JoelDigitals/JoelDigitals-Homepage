from decimal import Decimal
from django.db import migrations

# Neue Grundpreise fuer die zusaetzlichen Tech-Optionen (Wix/Squarespace/Webflow).
# TYPO3/Joomla/Magento bewusst ohne Zeile -> "Preis auf Anfrage" (spezialisierte/
# Enterprise-Systeme, bei denen ein Festpreis ohne Rueckfrage nicht sinnvoll ist.
NEW_BASE_OPTIONS = [
    ('onepager', 'wix', Decimal('490.00'), 1, Decimal('0.00')),
    ('onepager', 'squarespace', Decimal('490.00'), 1, Decimal('0.00')),
    ('onepager', 'webflow', Decimal('690.00'), 1, Decimal('0.00')),
    ('multipage', 'wix', Decimal('890.00'), 5, Decimal('40.00')),
    ('multipage', 'squarespace', Decimal('890.00'), 5, Decimal('40.00')),
    ('multipage', 'webflow', Decimal('1190.00'), 5, Decimal('50.00')),
]

ALL_TECHS = 'custom,wordpress,wix,squarespace,webflow,typo3,joomla,shopify,magento,other'
NON_CUSTOM_TECHS = 'wordpress,wix,squarespace,webflow,typo3,joomla,shopify,magento,other'

# Bestehende Features (aus 0002) hatten techs auf die damals 4 Tech-Werte
# begrenzt - jetzt auf die vollstaendige (erweiterte) Liste anheben, sonst
# waeren sie fuer Wix/Squarespace/... faelschlich unsichtbar.
EXISTING_FEATURE_TECHS_UPDATE = {
    'multilingual': ALL_TECHS, 'blog': ALL_TECHS, 'seo_basic': ALL_TECHS, 'seo_advanced': ALL_TECHS,
    'newsletter': ALL_TECHS, 'booking': ALL_TECHS, 'membership': ALL_TECHS,
    'product_filter': ALL_TECHS, 'payment_extra': ALL_TECHS, 'discounts': ALL_TECHS,
    'cms_training': NON_CUSTOM_TECHS, 'custom_design': NON_CUSTOM_TECHS,
}

# (key, name, category, price, site_types, techs, sort_order)
NEW_FEATURES = [
    # Inhalte
    ('faq', 'FAQ-Bereich', 'content', Decimal('150.00'), 'onepager,multipage,shop', ALL_TECHS, 1),
    ('portfolio', 'Portfolio/Referenzen-Galerie', 'content', Decimal('250.00'), 'onepager,multipage,shop', ALL_TECHS, 2),
    ('jobs', 'Jobs/Karriere-Seite', 'content', Decimal('300.00'), 'onepager,multipage,shop', ALL_TECHS, 3),
    ('press', 'Presse/News-Bereich', 'content', Decimal('200.00'), 'onepager,multipage,shop', ALL_TECHS, 4),
    ('maps', 'Anfahrt/Standort mit Google Maps', 'content', Decimal('100.00'), 'onepager,multipage,shop', ALL_TECHS, 5),

    # Design
    ('logo', 'Logo-Design', 'design', Decimal('350.00'), 'onepager,multipage,shop', ALL_TECHS, 1),
    ('illustrations', 'Individuelle Illustrationen/Grafiken', 'design', Decimal('400.00'), 'onepager,multipage,shop', ALL_TECHS, 2),
    ('photography', 'Professionelle Produktfotografie', 'design', Decimal('500.00'), 'onepager,multipage,shop', ALL_TECHS, 3),
    ('accessibility_design', 'Barrierefreies Design (WCAG-Grundlagen)', 'design', Decimal('300.00'), 'onepager,multipage,shop', ALL_TECHS, 4),

    # Marketing & SEO
    ('google_ads', 'Google Ads Tracking-Setup', 'marketing', Decimal('150.00'), 'onepager,multipage,shop', ALL_TECHS, 4),
    ('analytics', 'Analytics & Conversion-Tracking-Setup', 'marketing', Decimal('200.00'), 'onepager,multipage,shop', ALL_TECHS, 5),
    ('social', 'Social-Media-Integration', 'marketing', Decimal('100.00'), 'onepager,multipage,shop', ALL_TECHS, 6),
    ('local_seo', 'Local SEO / Google Unternehmensprofil', 'marketing', Decimal('180.00'), 'onepager,multipage,shop', ALL_TECHS, 7),

    # Shop-Funktionen
    ('shipping', 'Versanddienstleister-Integration (DHL, DPD, ...)', 'shop', Decimal('250.00'), 'shop', ALL_TECHS, 3),
    ('subscriptions', 'Abo-/Subscription-Produkte', 'shop', Decimal('400.00'), 'shop', ALL_TECHS, 4),
    ('reviews_feature', 'Produktbewertungen & Rezensionen', 'shop', Decimal('200.00'), 'shop', ALL_TECHS, 5),
    ('wishlist', 'Wishlist/Merkliste', 'shop', Decimal('150.00'), 'shop', ALL_TECHS, 6),
    ('multicurrency', 'Mehrere Währungen & internationaler Versand', 'shop', Decimal('350.00'), 'shop', ALL_TECHS, 7),

    # Technik
    ('livechat', 'Live-Chat-Integration', 'technik', Decimal('200.00'), 'onepager,multipage,shop', ALL_TECHS, 3),
    ('api_integration', 'Anbindung an Drittsysteme (API/CRM/ERP)', 'technik', Decimal('600.00'), 'onepager,multipage,shop', ALL_TECHS, 4),
    ('performance', 'Performance-Optimierung (Core Web Vitals)', 'technik', Decimal('300.00'), 'onepager,multipage,shop', ALL_TECHS, 5),
    ('backups', 'Automatisierte Backups', 'technik', Decimal('100.00'), 'onepager,multipage,shop', ALL_TECHS, 6),
    ('hosting_setup', 'Hosting & Domain-Einrichtung', 'technik', Decimal('100.00'), 'onepager,multipage,shop', ALL_TECHS, 7),

    # Recht & Sicherheit (neue Kategorie)
    ('legal_texts', 'Rechtssichere Rechtstexte (Impressum/Datenschutz/AGB)', 'legal', Decimal('250.00'), 'onepager,multipage,shop', ALL_TECHS, 0),
    ('cookie_consent', 'DSGVO-Cookie-Consent-Setup', 'legal', Decimal('120.00'), 'onepager,multipage,shop', ALL_TECHS, 1),
    ('ssl_security', 'SSL-Zertifikat & Sicherheits-Hardening', 'legal', Decimal('100.00'), 'onepager,multipage,shop', ALL_TECHS, 2),
]


def seed(apps, schema_editor):
    BasePricingOption = apps.get_model('website_configurator', 'BasePricingOption')
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')

    for site_type, tech, base_price, included_pages, extra_page_price in NEW_BASE_OPTIONS:
        BasePricingOption.objects.get_or_create(
            site_type=site_type, tech=tech,
            defaults={'base_price': base_price, 'included_pages': included_pages, 'extra_page_price': extra_page_price},
        )

    for key, techs in EXISTING_FEATURE_TECHS_UPDATE.items():
        ConfiguratorFeature.objects.filter(key=key).update(techs=techs)

    for key, name, category, price, site_types, techs, sort_order in NEW_FEATURES:
        ConfiguratorFeature.objects.get_or_create(
            key=key,
            defaults={'name': name, 'category': category, 'price': price,
                      'site_types': site_types, 'techs': techs, 'sort_order': sort_order},
        )


def unseed(apps, schema_editor):
    BasePricingOption = apps.get_model('website_configurator', 'BasePricingOption')
    ConfiguratorFeature = apps.get_model('website_configurator', 'ConfiguratorFeature')
    BasePricingOption.objects.filter(
        site_type__in=[o[0] for o in NEW_BASE_OPTIONS], tech__in=[o[1] for o in NEW_BASE_OPTIONS]
    ).delete()
    ConfiguratorFeature.objects.filter(key__in=[f[0] for f in NEW_FEATURES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0003_alter_basepricingoption_tech_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
