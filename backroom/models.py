from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

class BackroomProduct(models.Model):
    name = models.CharField(max_length=200, verbose_name="Produktname (DE)")
    name_english = models.CharField(max_length=200, blank=True, null=True, verbose_name="Product name (EN)")
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Beschreibung (DE)", blank=True)
    description_english = models.TextField(verbose_name="Description (EN)", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="EK-Preis (€)",
        help_text="Einkaufspreis - das zahlt der Partner im Backroom.")
    uvp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="UVP (€)",
        help_text="Unverbindliche Preisempfehlung - regulärer Verkaufspreis, dient nur zum Vergleich/Anzeige.")
    image = models.URLField(max_length=500, blank=True, null=True, verbose_name="Bild-URL")
    is_published = models.BooleanField(default=True, verbose_name="Veröffentlicht")
    order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")

    discount_start = models.DateTimeField(blank=True, null=True, verbose_name="Rabatt Start")
    discount_end = models.DateTimeField(blank=True, null=True, verbose_name="Rabatt Ende")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Rabatt (%)")
    requires_activation = models.BooleanField(
        default=False,
        verbose_name="Benötigt Aktivierung",
        help_text="Z.B. Softwarelizenzen: Käufer muss nach dem Kauf einen Aktivierungscode erhalten. "
                   "Siehe backroom/ACTIVATION.md für die Einbindung in den Checkout-Ablauf."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Backroom Produkt"
        verbose_name_plural = "Backroom Produkte"

    @property
    def discount_is_active(self):
        """Prüft, ob ein Rabatt auf den EK-Preis aktuell gültig ist."""
        now = timezone.now()
        if self.discount_percent <= 0:
            return False
        if self.discount_start and now < self.discount_start:
            return False
        if self.discount_end and now > self.discount_end:
            return False
        return True

    @property
    def discounted_price(self):
        """EK-Preis nach Rabatt, nur wenn Rabatt aktiv ist."""
        if self.price and self.discount_is_active:
            multiplier = Decimal(1) - (Decimal(self.discount_percent) / Decimal(100))
            return self.price * multiplier
        return self.price

    @property
    def savings_amount(self):
        """Ersparnis gegenüber der UVP (falls gesetzt)."""
        if not self.uvp:
            return None
        return max(self.uvp - self.discounted_price, Decimal('0'))

    @property
    def savings_percent(self):
        if not self.uvp or self.uvp <= 0:
            return None
        return int((self.savings_amount / self.uvp) * 100)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.name
            slug = slugify(base)
            if not slug:
                slug = f"product-{BackroomProduct.objects.count() + 1}"
            while BackroomProduct.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slugify(base)}-{BackroomProduct.objects.count() + 1}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BackroomAccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('approved', 'Genehmigt'),
        ('rejected', 'Abgelehnt'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='backroom_access_requests'
    )
    message = models.TextField(
        blank=True, verbose_name="Nachricht",
        help_text="Warum möchtest du Zugang zum Backroom (EK-Shop) erhalten?"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, verbose_name="Admin-Notiz")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Backroom Zugangsanfrage"
        verbose_name_plural = "Backroom Zugangsanfragen"

    def approve(self):
        from .access import BACKROOM_GROUP_NAME
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=BACKROOM_GROUP_NAME)
        self.user.groups.add(group)
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])

    def reject(self, note=""):
        self.status = 'rejected'
        if note:
            self.admin_note = note
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'admin_note', 'processed_at'])

    def __str__(self):
        return f"{self.user.username} – {self.get_status_display()}"
