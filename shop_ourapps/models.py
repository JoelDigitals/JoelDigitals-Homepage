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

    def transfer_to_wallet(self):
        self.balance += self.pending_earnings
        self.pending_earnings = Decimal('0.00')
        self.save()

    def __str__(self):
        return f"{self.user.email} – Balance: {self.balance} €, Pending: {self.pending_earnings} €"
    
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

    discount_percent = models.PositiveIntegerField(default=0)

    @property
    def discounted_price(self):
        if self.price and self.discount_percent > 0:
            discount_multiplier = Decimal(1) - (Decimal(self.discount_percent) / Decimal(100))
            return self.price * discount_multiplier
        return self.price

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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # <--- hinzugefügt

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    affiliate_code = models.ForeignKey('AffiliateCode', on_delete=models.SET_NULL, null=True, blank=True)
    discount_code = models.ForeignKey('DiscountCode', on_delete=models.SET_NULL, null=True, blank=True)

    account_holder = models.CharField(max_length=255, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True)
    bic = models.CharField(max_length=11, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bestellung {self.id} von {self.user}"

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