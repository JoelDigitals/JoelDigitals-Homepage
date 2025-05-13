from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class App(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    version = models.CharField(max_length=20)
    image = models.ImageField(upload_to='app_images/', null=True, blank=True)
    is_available_for_purchase = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

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


# ... (alle bisherigen Klassen wie App, AffiliateLink, Purchase etc.)

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Banküberweisung'),
        ('invoice', 'Rechnung'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=100, default='Pending')  # 'Pending', 'Paid'
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Offen'), ('paid', 'Bezahlt')], default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Preis zum Zeitpunkt der Bestellung

    def __str__(self):
        return f"{self.app.name} x {self.quantity} (Order {self.order.id})"
