from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid

User = get_user_model()

def generate_voucher_code():
    return '-'.join([
        uuid.uuid4().hex.upper()[i:i+4]
        for i in range(0, 16, 4)
    ])

class Voucher(models.Model):
    code = models.CharField(max_length=19, unique=True, default=generate_voucher_code)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class VoucherOrder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voucher = models.OneToOneField('Voucher', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # Neue Felder für Rechnungsversand
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=255)
    message = models.TextField(blank=True, help_text="Optional personal message")

class AppGroup(models.Model):
    key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class AffiliatePartner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    website = models.URLField(blank=True)
    social_links = models.TextField(blank=True, help_text="One link per line")
    application_text = models.TextField()
    commission_percent = models.PositiveIntegerField(default=3, help_text="Provision in Prozent")  # z. B.3%
    approved = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Noch nicht ausgezahlt

    def add_earnings(self, amount):
        self.pending_earnings += Decimal(amount)
        self.save()

    def has_funds(self, amount):
        return self.balance >= amount

    def deduct(self, amount):
        if self.has_funds(amount):
            self.balance -= Decimal(amount)
            self.save()
            return True
        return False

    def __str__(self):
        return f"Wallet von {self.user.username}"


class CustomerInfo(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_info')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"


class WalletCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def redeem(self, user):
        if not self.is_used:
            wallet, created = Wallet.objects.get_or_create(user=user)
            wallet.add_credit(self.value)
            self.is_used = True
            self.used_by = user
            self.used_at = timezone.now()
            self.save()
            return True
        return False

class SaleBadge(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="sale_badges/")

    def __str__(self):
        return self.name

class App(models.Model):
    name = models.CharField(max_length=255)
    name_english = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    description_english = models.TextField(blank=True, null=True)
    product_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    version = models.CharField(max_length=20)
    image = models.ImageField(upload_to='app_images/', null=True, blank=True)
    is_available_for_purchase = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Neue App-Store Links
    android_link = models.URLField(blank=True, null=True)
    ios_link = models.URLField(blank=True, null=True)
    windows_link = models.URLField(blank=True, null=True)
    macos_link = models.URLField(blank=True, null=True)
    linux_link = models.URLField(blank=True, null=True)

    link = models.URLField(blank=True, null=True)
    group = models.ForeignKey(AppGroup, null=True, blank=True, on_delete=models.SET_NULL)

    is_black_week = models.BooleanField(default=False)
    is_cyber_monday = models.BooleanField(default=False)
    is_christmas_sale = models.BooleanField(default=False)

    sale_badge = models.ForeignKey(SaleBadge, null=True, blank=True, on_delete=models.SET_NULL)

    # Rabatt nur innerhalb eines Zeitraums gültig
    discount_start = models.DateTimeField(blank=True, null=True)
    discount_end = models.DateTimeField(blank=True, null=True)
    discount_percent = models.PositiveIntegerField(default=0)

    @property
    def discount_is_active(self):
        """Prüft, ob Rabatt aktuell gültig ist."""
        from django.utils import timezone

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
        """Berechnet den Preis, nur wenn Rabatt aktiv ist."""
        from decimal import Decimal

        if self.price and self.discount_is_active:
            discount_multiplier = Decimal(1) - (Decimal(self.discount_percent) / Decimal(100))
            return self.price * discount_multiplier

        return self.price

    @property
    def active_sale_name(self):
        """Gibt den Namen des aktiven Sales zurück."""
        if self.is_black_week:
            return "Black Week Deal"
        if self.is_cyber_monday:
            return "Cyber Monday Deal"
        if self.is_christmas_sale:
            return "Christmas Sale"
        return None

    refundable = models.BooleanField(
        default=False,
        help_text="Kann diese App zurückerstattet werden?"
    )

    exchangeable = models.BooleanField(
        default=False,
        help_text="Kann diese App umgetauscht werden?"
    )

    is_physical = models.BooleanField(default=False, help_text="Ist dies ein physisches Produkt?")
    requires_shipping = models.BooleanField(default=False, help_text="Benötigt dieses Produkt einen Versand?")
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Gewicht in kg")
    stock = models.IntegerField(default=0, help_text="Lagerbestand (0 = nicht auf Lager)")
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Versandkosten (einmalig pro Bestellung)")

    def __str__(self):
        return self.name 


class AffiliateLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    commission_percent = models.PositiveIntegerField(default=5)  # z. B. 10%

    def __str__(self):
        return f"{self.user.username} - {self.code}"


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    affiliate = models.ForeignKey(AffiliateLink, null=True, blank=True, on_delete=models.SET_NULL)

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    address = models.TextField()
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.full_name} - {self.app.name}"

class Affiliate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    youtube_subscribers = models.IntegerField(default=0)
    instagram_followers = models.IntegerField(default=0)
    facebook_likes = models.IntegerField(default=0)
    tik_tok_followers = models.IntegerField(default=0)
    twitter_followers = models.IntegerField(default=0)
    twitch_followers = models.IntegerField(default=0)
    points = models.IntegerField(default=0)  # Berechnete Punkte

    def calculate_points(self):
        # Berechnung der Punkte (Beispiel: 1 Punkt pro 100 Abonnenten/Follower)
        self.points = (self.youtube_subscribers // 100) + (self.instagram_followers // 100) + (self.facebook_likes // 100) + (self.tik_tok_followers // 100) + (self.twitter_followers // 100) + (self.twitch_followers // 100)
        self.save()

    def is_eligible(self):
        return self.points >= 1000

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.price * self.quantity


# ... (alle bisherigen Klassen wie App, AffiliateLink, Purchase etc.)

class Order(models.Model):
    STATUS_CHOICES = [
        ('Received', 'Received'),
        ('Paid', 'Paid'),
        ('Return', 'Return'),
        ('Canceled', 'Canceled'),
        ('Back', 'Back at Joel Digitals'),
        ('In Delivery', 'In Delivery'),
        ('Delivered', 'Delivered'),
        ('Finished', 'Finished'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    vat_number = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=50)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Received')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    affiliate_code = models.ForeignKey('AffiliateCode', on_delete=models.SET_NULL, null=True, blank=True)
    discount_code = models.ForeignKey('DiscountCode', on_delete=models.SET_NULL, null=True, blank=True)

    sepa_mandate_ref = models.CharField(max_length=64, blank=True, null=True, help_text="SEPA-Mandatsreferenz")
    sepa_mandate_date = models.DateTimeField(blank=True, null=True, help_text="Datum des SEPA-Mandats")

    account_holder = models.CharField(max_length=255, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True)
    bic = models.CharField(max_length=11, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    # Neue Felder für Automatisierung
    registration_code = models.CharField(max_length=255, blank=True, null=True, help_text="Registrierungscode für den Versand")
    registration_code_sent_at = models.DateTimeField(null=True, blank=True, help_text="Zeitpunkt, wann der Registrierungscode gesendet wurde")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="Automatisch auf 30 Min nach registration_code_sent_at gesetzt")
    review_email_sent_at = models.DateTimeField(null=True, blank=True, help_text="Zeitpunkt, wann Review-Email gesendet wurde")
    review_email_scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Geplante Zeit zum Versand der Review-Email (12-30 Stunden nach delivered_at)")

    def __str__(self):
        return f"Bestellung {self.id} von {self.user}"
    
    def schedule_review_email(self):
        """Plant den Versand der Review-Email für 12-30 Stunden nach Lieferung."""
        import random
        if self.delivered_at and not self.review_email_scheduled_for:
            # Zufälliger Verzug zwischen 12-30 Stunden
            random_hours = random.randint(12, 72)
            self.review_email_scheduled_for = self.delivered_at + timezone.timedelta(hours=random_hours)
            self.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.affiliate_code and self.total_amount > 0:
            partner = self.affiliate_code.partner
            provision_prozent = partner.commission_percent
            provision_betrag = (Decimal(provision_prozent) / Decimal(100)) * self.total_amount

            wallet, _ = Wallet.objects.get_or_create(user=partner.user)
            wallet.add_earnings(provision_betrag)

            AffiliateTransaction.objects.create(
                partner=partner,
                order=self,
                amount=provision_betrag
            )

class AffiliateTransaction(models.Model):
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    discount_percent = models.PositiveIntegerField(default=0)
    single_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)  # Preis nach Rabatt2
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Preis zum Zeitpunkt der Bestellung

    def __str__(self):
        return f"{self.app.name} x {self.quantity} (Order {self.order.id})"

class AffiliateCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    partner = models.ForeignKey("AffiliatePartner", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    times_used = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    def update_status(self):
        """Aktiviert oder deaktiviert den Code basierend auf Zeit."""
        now = timezone.now()

        # Aktivieren, wenn Startzeit erreicht
        if self.valid_from and now >= self.valid_from:
            self.is_active = True

        # Deaktivieren, wenn Endzeit überschritten
        if self.valid_until and now > self.valid_until:
            self.is_active = False

        self.save()

    def is_valid_now(self):
        """Prüft, ob der Code aktuell verwendet werden darf."""
        now = timezone.now()
        return (
            self.is_active and
            (self.valid_from is None or self.valid_from <= now) and
            (self.valid_until is None or now <= self.valid_until)
        )

    def __str__(self):
        return self.code


class OrderStatusLog(models.Model):
    """Log für Status-Übergänge und automatische Ereignisse."""
    STATUS_CHOICES = [
        ('status_changed', 'Status geändert'),
        ('registration_code_sent', 'Registrierungscode gesendet'),
        ('auto_delivered', 'Automatisch als geliefert markiert'),
        ('review_email_scheduled', 'Review-Email geplant'),
        ('review_email_sent', 'Review-Email gesendet'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    event_type = models.CharField(max_length=50, choices=STATUS_CHOICES)
    old_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50, blank=True, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order {self.order.id} - {self.event_type} am {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']

class ReturnRequest(models.Model):
    REASON_CHOICES = [
        # Technisch
        ('not_working',       'App funktioniert nicht / Startet nicht'),
        ('technical_issue',   'Technisches Problem (Bug, Absturz)'),
        ('install_failed',    'Installation fehlgeschlagen'),
        # Bestellfehler
        ('wrong_product',     'Falsches Produkt erhalten'),
        ('duplicate',         'Versehentlich doppelt bestellt'),
        ('wrong_version',     'Falsche Version / Plattform'),
        # Inhalt
        ('not_as_described',  'Entspricht nicht der Beschreibung'),
        ('missing_feature',   'Erwartete Funktion fehlt'),
        ('language_issue',    'Sprachproblem / Falsche Sprache'),
        # Sonstige
        ('changed_mind',      'Meinung geändert / nicht mehr benötigt'),
        ('price_issue',       'Preisproblem / günstiger anderswo'),
        ('other',             'Sonstiges'),
    ]
    STATUS_CHOICES = [
        ('pending',    'Ausstehend – Prüfung läuft'),
        ('approved',   'Genehmigt'),
        ('rejected',   'Abgelehnt'),
        ('processing', 'In Bearbeitung'),
        ('completed',  'Abgeschlossen – Erstattet'),
    ]

    # Gründe: automatisch genehmigt wenn Bedingungen erfüllt
    AUTO_APPROVE_REASONS  = ['not_working', 'wrong_product', 'duplicate', 'wrong_version', 'install_failed']
    # Gründe: immer manuell prüfen
    MANUAL_REVIEW_REASONS = ['technical_issue', 'not_as_described', 'missing_feature', 'language_issue']
    # Gründe: nur genehmigt wenn App refundable
    REFUND_ONLY_REASONS   = ['changed_mind', 'price_issue', 'other']

    RETURN_TYPE_CHOICES = [
        ('refund',   'Rückerstattung'),
        ('exchange', 'Umtausch / Austausch'),
    ]
    return_type = models.CharField(
        max_length=20, choices=RETURN_TYPE_CHOICES, default='refund',
        verbose_name='Art des Antrags'
    )
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason      = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(max_length=1000, blank=True, verbose_name='Beschreibung')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note  = models.TextField(blank=True, verbose_name='Admin-Notiz')

    # Sendungsverfolgung (falls physische Rücksendung nötig)
    tracking_number  = models.CharField(max_length=100, blank=True, verbose_name='Sendungsnummer')
    tracking_carrier = models.CharField(max_length=50, blank=True, verbose_name='Carrier',
                        help_text='z.B. DHL, UPS, DPD, Hermes')
    tracking_url     = models.URLField(blank=True, verbose_name='Tracking-URL',
                        help_text='Direktlink zur Sendungsverfolgung')
    return_label_url = models.URLField(blank=True, verbose_name='Retourenschein-URL')

    # Erstattung
    refund_amount    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                        verbose_name='Erstattungsbetrag (€)')
    refund_method    = models.CharField(max_length=50, blank=True, verbose_name='Erstattungsmethode',
                        help_text='z.B. Stripe, PayPal, Wallet, Überweisung')
    refunded_at      = models.DateTimeField(null=True, blank=True, verbose_name='Erstattet am')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def auto_evaluate(self):
        """
        Wertet den Antrag automatisch aus. Prüft echte Bedingungen:
        - duplicate: war diese App wirklich mehrfach bestellt?
        - wrong_product: welches Produkt wurde erwartet?
        - refundable: ist die App erstattbar?
        """
        from django.db.models import Count
        reason = self.reason
        order  = self.order

        # Duplikat-Check: hat der User dieselbe App in einer anderen bezahlten Bestellung?
        if reason == 'duplicate':
            app_ids = list(order.items.values_list('app_id', flat=True))
            duplicate_orders = Order.objects.filter(
                user=order.user,
                status__in=['Paid', 'In Delivery', 'Delivered', 'Finished'],
                items__app_id__in=app_ids,
            ).exclude(id=order.id).distinct()
            if not duplicate_orders.exists():
                # Kein echter Duplikat gefunden → manuelle Prüfung
                self.status = 'pending'
                self.admin_note = (
                    self.admin_note +
                    ' [Auto] Kein Duplikat gefunden – manuelle Prüfung erforderlich.'
                ).strip()
                self.save(update_fields=['status', 'admin_note', 'updated_at'])
                return self.status

        all_refundable = all(
            item.app.refundable for item in order.items.select_related('app')
        )

        if reason in self.AUTO_APPROVE_REASONS:
            self.status = 'approved'
        elif reason in self.REFUND_ONLY_REASONS:
            self.status = 'approved' if all_refundable else 'rejected'
            if not all_refundable:
                self.admin_note = (
                    self.admin_note +
                    ' [Auto] Abgelehnt: Apps nicht als rückerstattbar markiert.'
                ).strip()
        else:
            # MANUAL_REVIEW_REASONS und alles andere
            self.status = 'pending'

        self.save(update_fields=['status', 'admin_note', 'updated_at'])
        return self.status

    @property
    def tracking_info(self):
        """Gibt verfügbare Tracking-Infos zurück."""
        if self.tracking_url:
            return {'url': self.tracking_url, 'number': self.tracking_number, 'carrier': self.tracking_carrier}
        if self.tracking_number and self.tracking_carrier:
            carrier_urls = {
                'DHL':    f'https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={self.tracking_number}',
                'UPS':    f'https://www.ups.com/track?tracknum={self.tracking_number}',
                'DPD':    f'https://tracking.dpd.de/status/de_DE/parcel/{self.tracking_number}',
                'Hermes': f'https://www.myhermes.de/empfangen/sendungsverfolgung/sendungsinformation/?trackingNumber={self.tracking_number}',
                'GLS':    f'https://gls-group.eu/track/{self.tracking_number}',
            }
            url = carrier_urls.get(self.tracking_carrier, '')
            return {'url': url, 'number': self.tracking_number, 'carrier': self.tracking_carrier}
        return None

    def __str__(self):
        return f"Rücksendung #{self.id} – #{self.order.id} ({self.get_reason_display()}) [{self.get_status_display()}]"


class ShipmentTracking(models.Model):
    """Sendungsverfolgung für Bestellungen (Outbound Delivery)."""
    CARRIER_CHOICES = [
        ('DHL',     'DHL'),
        ('UPS',     'UPS'),
        ('DPD',     'DPD'),
        ('Hermes',  'Hermes'),
        ('GLS',     'GLS'),
        ('FedEx',   'FedEx'),
        ('PostAG',  'Österreichische Post'),
        ('Swiss',   'Swiss Post'),
        ('custom',  'Sonstiger Carrier'),
    ]
    order           = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    carrier         = models.CharField(max_length=20, choices=CARRIER_CHOICES)
    tracking_number = models.CharField(max_length=100)
    tracking_url    = models.URLField(blank=True, help_text='Wenn leer, wird auto-generiert')
    dispatched_at   = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True, verbose_name='Voraussichtliche Lieferung')
    note            = models.CharField(max_length=255, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    CARRIER_URL_TEMPLATES = {
        'DHL':    'https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={n}',
        'UPS':    'https://www.ups.com/track?tracknum={n}',
        'DPD':    'https://tracking.dpd.de/status/de_DE/parcel/{n}',
        'Hermes': 'https://www.myhermes.de/empfangen/sendungsverfolgung/sendungsinformation/?trackingNumber={n}',
        'GLS':    'https://gls-group.eu/track/{n}',
        'FedEx':  'https://www.fedex.com/fedextrack/?trknbr={n}',
    }

    @property
    def resolved_tracking_url(self):
        if self.tracking_url:
            return self.tracking_url
        tpl = self.CARRIER_URL_TEMPLATES.get(self.carrier, '')
        return tpl.format(n=self.tracking_number) if tpl else ''

    def __str__(self):
        return f"Sendung {self.carrier} {self.tracking_number} (Order #{self.order.id})"


class AppReview(models.Model):
    """Produktbewertung für eine App. Nur eingeloggte Käufer können bewerten."""

    STARS_CHOICES = [(i, f"{i} Stern{'e' if i != 1 else ''}") for i in range(0, 6)]

    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='app_reviews')
    stars = models.PositiveSmallIntegerField(choices=STARS_CHOICES)
    comment = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        unique_together = ('app', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.app.name}: {self.stars}★"
