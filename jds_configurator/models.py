# jds_configurator/models.py
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class JdsModule(models.Model):
    """Ein Modul von 'Dein individuelles JDS Management'. Kern-Module (is_core)
    bilden gemeinsam das verpflichtende Basismodul (fester Gesamtpreis, siehe
    JdsConfigRequest.BASISMODUL_PRICE) - sie werden auf der Konfigurator-Seite nur
    aufgelistet, nicht einzeln ausgewählt/bepreist. Nicht-Kern-Module sind
    zubuchbare Add-ons mit eigenem einmaligen Preis (kein Abo)."""
    CATEGORY_CHOICES = [
        ('basis', 'Basis'),
        ('verkauf', 'Verkauf'),
        ('personal', 'Personal'),
        ('fuhrpark', 'Fuhrpark'),
        ('produktion', 'Produktion'),
        ('organisation', 'Organisation'),
        ('it', 'IT'),
    ]
    key = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basis')
    description = models.CharField(max_length=255, blank=True)
    is_core = models.BooleanField(default=False, help_text="Teil des verpflichtenden Basismoduls")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Einmaliger Preis (kein Abo)")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return self.name


# Staffelpreis für zusätzliche User: fällt linear vom Preis des ersten
# Zusatz-Users um je EXTRA_USER_PRICE_STEP pro weiterem User, mindestens aber
# EXTRA_USER_MIN_PRICE. Alles einmalig, kein Abo.
EXTRA_USER_FIRST_PRICE = Decimal('6.45')
EXTRA_USER_PRICE_STEP = Decimal('0.825')
EXTRA_USER_MIN_PRICE = Decimal('2.00')


def extra_user_unit_price(index):
    """Preis für den n-ten (1-basiert) zusätzlichen User."""
    price = EXTRA_USER_FIRST_PRICE - EXTRA_USER_PRICE_STEP * (index - 1)
    return max(price, EXTRA_USER_MIN_PRICE)


def extra_users_total(count):
    """Summe über die Staffelpreise der ersten `count` Zusatz-User."""
    return sum((extra_user_unit_price(i) for i in range(1, count + 1)), Decimal('0.00'))


def calculate_totals(basismodul_price, addon_modules, extra_users=0):
    """Zentrale Preisberechnung fuer Basismodul + Zusatzmodule + zubuchbare User
    (alles einmalig, kein Rabattcode - der wird erst im Shop-Checkout angegeben).
    Wird sowohl von JdsConfigRequest (Beratung/Angebot) als auch von
    JdsConfiguration (Warenkorb/Checkout) verwendet."""
    addon_total = sum((m.price for m in addon_modules), Decimal('0.00'))
    user_total = extra_users_total(extra_users)
    return basismodul_price + addon_total + user_total


class JdsConfigRequest(models.Model):
    BASISMODUL_PRICE = Decimal('59.99')
    INCLUDED_USERS = 6

    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('approved', 'Genehmigt'),
        ('rejected', 'Abgelehnt'),
    ]
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Überweisung'),
        ('paypal', 'PayPal'),
    ]

    reference = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Kundendaten
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)

    modules = models.ManyToManyField(JdsModule, related_name='requests', blank=True)
    extra_users = models.PositiveIntegerField(default=0, help_text=f"Zusätzliche User über die im Basismodul enthaltenen {INCLUDED_USERS} hinaus")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True, help_text="Anmerkungen des Kunden")
    internal_notes = models.TextField(blank=True, help_text="Interne Notizen (nur für Plattform-Admins)")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, help_text="Bei Genehmigung gewählte Zahlungsart")
    order = models.ForeignKey('shop_ourapps.Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='jds_config_requests')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"JDS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def addon_modules(self):
        return self.modules.filter(is_core=False)

    def recalculate_totals(self):
        """Berechnet total_amount neu aus den aktuell zugeordneten Modulen +
        Zusatz-Usern. Speichert NICHT selbst."""
        self.total_amount = calculate_totals(self.BASISMODUL_PRICE, self.addon_modules, self.extra_users)


class JdsConfiguration(models.Model):
    """Preis-Snapshot einer Konfigurator-Auswahl (Module + Zusatz-User), die über
    'In den Warenkorb' im normalen Shop-Checkout gekauft wird (siehe
    shop_ourapps.CartItem.jds_configuration / OrderItem.jds_configuration).
    Anders als JdsConfigRequest enthält sie keine Kundendaten - die werden erst
    im regulären Checkout erfasst - und durchläuft keine manuelle Genehmigung."""
    modules = models.ManyToManyField(JdsModule, related_name='cart_configurations', blank=True)
    extra_users = models.PositiveIntegerField(default=0)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    @property
    def addon_modules(self):
        return self.modules.filter(is_core=False)

    @property
    def display_name(self):
        parts = [f"{self.addon_modules.count()} Zusatzmodul(e)"]
        if self.extra_users:
            parts.append(f"{self.extra_users} Zusatz-User")
        return f"JDS Management individuell ({', '.join(parts)})"

    def recalculate_totals(self):
        self.total_amount = calculate_totals(JdsConfigRequest.BASISMODUL_PRICE, self.addon_modules, self.extra_users)


class JdsFeatureRequest(models.Model):
    """Wunsch nach einer individuellen Zusatzentwicklung, die es (noch) nicht als
    fertiges Modul gibt - kein Kaufvorgang, sondern eine Anfrage zur manuellen
    Prüfung durch Joel Digitals. Bei Genehmigung wird eine ungefähre
    Verfügbarkeitsdauer angegeben und der Kunde per Mail benachrichtigt."""
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('in_review', 'In Prüfung'),
        ('approved', 'Genehmigt'),
        ('rejected', 'Abgelehnt'),
    ]

    reference = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)

    description = models.TextField(help_text="Gewünschte Zusatzfunktion(en) in eigenen Worten des Kunden")

    internal_notes = models.TextField(blank=True, help_text="Interne Notizen / Rückfragen (nur Plattform-Admins)")
    estimated_availability = models.CharField(
        max_length=100, blank=True,
        help_text="z.B. 'ca. 4-6 Wochen' - bei Genehmigung angeben, wird dem Kunden mitgeteilt"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"JDSF-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
