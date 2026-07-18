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
    zubuchbare Add-ons mit eigenem monatlichen Preis."""
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
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return self.name


class JdsConfigRequest(models.Model):
    BASISMODUL_PRICE = Decimal('59.99')

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

    discount_code = models.ForeignKey('shop_ourapps.DiscountCode', null=True, blank=True, on_delete=models.SET_NULL)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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

    def recalculate_totals(self, discount_code=None):
        """Berechnet subtotal/discount_amount/total_amount neu aus den aktuell
        zugeordneten Modulen + optionalem Rabattcode. Speichert NICHT selbst."""
        addon_total = sum((m.monthly_price for m in self.addon_modules), Decimal('0.00'))
        subtotal = self.BASISMODUL_PRICE + addon_total
        discount = Decimal('0.00')
        if discount_code and discount_code.is_valid_now():
            discount = (subtotal * discount_code.percentage / Decimal('100')).quantize(Decimal('0.01'))
        self.subtotal = subtotal
        self.discount_amount = discount
        self.total_amount = max(Decimal('0.00'), subtotal - discount)
