# website_configurator/models.py
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class BasePricingOption(models.Model):
    """Grundpreis für eine Kombination aus Website-Typ und Umsetzung/Technologie.
    Admin-editierbar (siehe admin.py), damit Preise ohne Code-Änderung angepasst
    werden können. Fehlt eine (aktive) Zeile für eine Kombination, oder ist
    base_price=0, bedeutet das 'Preis auf Anfrage' (siehe calculate_totals) -
    so können neue/exotische Tech-Optionen angeboten werden, ohne dass sofort
    ein Festpreis dafür existieren muss."""
    SITE_TYPE_CHOICES = [
        ('onepager', 'Onepager'),
        ('multipage', 'Mehrseitige Homepage'),
        ('shop', 'Online-Shop'),
    ]
    TECH_CHOICES = [
        ('custom', 'Programmiert (Custom Code)'),
        ('wordpress', 'WordPress'),
        ('wix', 'Wix'),
        ('shopify', 'Shopify'),
        ('other', 'Anderes System'),
    ]
    # Für welche Website-Typen eine Tech-Option im Wizard überhaupt angeboten
    # wird (Kommagetrennt aus SITE_TYPE_CHOICES) - z.B. Shopify nur für 'shop'.
    TECH_SITE_TYPES = {
        'custom': 'onepager,multipage,shop',
        'wordpress': 'onepager,multipage,shop',
        'wix': 'onepager,multipage',
        'shopify': 'shop',
        'other': 'onepager,multipage,shop',
    }

    site_type = models.CharField(max_length=20, choices=SITE_TYPE_CHOICES)
    tech = models.CharField(max_length=20, choices=TECH_CHOICES)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Einmaliger Grundpreis. 0 = Preis auf Anfrage")
    included_pages = models.PositiveIntegerField(default=1, help_text="Inklusive Unterseiten (nur relevant bei 'Mehrseitige Homepage')")
    extra_page_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Preis je weiterer Unterseite über die inklusiven hinaus")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('site_type', 'tech')]
        ordering = ['site_type', 'tech']

    def __str__(self):
        return f"{self.get_site_type_display()} – {self.get_tech_display()}"


class ConfiguratorFeature(models.Model):
    """Zubuchbares Zusatzfeature im Website-Konfigurator, admin-editierbar.
    site_types/techs sind kommagetrennte Listen der Werte aus
    BasePricingOption.SITE_TYPE_CHOICES/TECH_CHOICES, für die das Feature
    im Wizard überhaupt wählbar ist (z.B. Shop-Features nur bei 'shop')."""
    CATEGORY_CHOICES = [
        ('content', 'Inhalte'),
        ('design', 'Design'),
        ('marketing', 'Marketing & SEO'),
        ('shop', 'Shop-Funktionen'),
        ('technik', 'Technik'),
        ('legal', 'Recht & Sicherheit'),
    ]

    key = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='content')
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Einmaliger Aufpreis")
    site_types = models.CharField(max_length=100, default='onepager,multipage,shop', help_text="Kommagetrennt, z.B. 'shop' für reine Shop-Features")
    techs = models.CharField(max_length=100, default='custom,wordpress,wix,squarespace,webflow,typo3,joomla,shopify,magento,other', help_text="Kommagetrennt, z.B. 'wordpress,shopify' für reine CMS-Features")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return self.name

    def applies_to(self, site_type, tech):
        return (
            site_type in [s.strip() for s in self.site_types.split(',') if s.strip()]
            and tech in [t.strip() for t in self.techs.split(',') if t.strip()]
        )


def calculate_totals(base_option, features, page_count=0):
    """Zentrale Preisberechnung: Grundpreis + Zusatzseiten-Aufpreis + Feature-Summe.
    Einzige Quelle der Wahrheit für den Preis - der Client schickt im Wizard nur
    die Auswahl, nie den Preis selbst. Gibt None zurück, wenn kein (aktiver)
    Grundpreis existiert bzw. dieser 0 ist ('Preis auf Anfrage')."""
    if base_option is None or not base_option.base_price:
        return None
    total = base_option.base_price
    if page_count and base_option.included_pages:
        extra_pages = max(0, page_count - base_option.included_pages)
        total += extra_pages * base_option.extra_page_price
    total += sum((f.price for f in features), Decimal('0.00'))
    return total


class WebsiteConfigRequest(models.Model):
    """Lead/Anfrage aus dem Website-Konfigurator. Kein Kaufvorgang - der
    Interessent erhält einen Preisvorschlag und das Vertriebsteam wird
    benachrichtigt, die weitere Abwicklung (Angebot, Vertrag) läuft manuell.

    Da die Kontaktdaten im Wizard als Erstes abgefragt werden, wird der
    Datensatz bereits nach Schritt 1 als 'draft' angelegt und bei jedem
    weiteren Wizard-Schritt per AJAX aktualisiert (siehe views.save_contact/
    update_draft) - so bleibt der Lead auch bei Abbruch vor dem finalen
    Absenden für den Vertrieb sichtbar. site_type/tech sind deshalb blank=True
    (zum Zeitpunkt der Draft-Erstellung noch nicht gewählt)."""
    STATUS_CHOICES = [
        ('draft', 'Entwurf (nicht abgeschlossen)'),
        ('pending', 'Ausstehend'),
        ('in_review', 'In Prüfung'),
        ('contacted', 'Kontaktiert'),
        ('won', 'Gewonnen'),
        ('lost', 'Verloren'),
    ]

    reference = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    site_type = models.CharField(max_length=20, choices=BasePricingOption.SITE_TYPE_CHOICES, blank=True)
    tech = models.CharField(max_length=20, choices=BasePricingOption.TECH_CHOICES, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True, help_text="Nur bei 'Mehrseitige Homepage' relevant")
    features = models.ManyToManyField(ConfiguratorFeature, related_name='requests', blank=True)

    estimated_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leer = Preis auf Anfrage bzw. noch nicht berechnet")

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, help_text="Pflichtfeld - für Rückfragen zum verbindlichen Auftrag")
    company_name = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True, help_text="Anmerkungen des Interessenten")

    terms_accepted = models.BooleanField(default=False, help_text="Kunde hat beim verbindlichen Absenden AGB/Datenschutz akzeptiert")
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    internal_notes = models.TextField(blank=True, help_text="Interne Notizen (nur für Plattform-Admins)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"WEB-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """Berechnet estimated_total neu aus Website-Typ/Tech/Seitenzahl/Features.
        Speichert NICHT selbst (analog jds_configurator-Konvention). Ohne
        Website-Typ/Tech (z.B. noch unvollständiger Draft) bleibt der Preis leer."""
        if not self.site_type or not self.tech:
            self.estimated_total = None
            return
        base_option = BasePricingOption.objects.filter(
            site_type=self.site_type, tech=self.tech, is_active=True
        ).first()
        self.estimated_total = calculate_totals(base_option, self.features.all(), self.page_count or 0)


class EmailTemplate(models.Model):
    """Vorlage fuer die 'Mail versenden'-Seite im Anfragen-Admin (admin_views.
    request_send_mail) - admin-editierbar, damit der Vertrieb eigene
    Textbausteine pflegen kann, ohne Code aendern zu muessen. Platzhalter in
    subject/body werden per str.format() ersetzt: {name}, {reference},
    {site_type}, {tech}, {estimated_total}, {company_name}."""
    name = models.CharField(max_length=100, help_text="Interner Name zur Auswahl, z.B. 'Rückfrage zur Anfrage'")
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name
