from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .models import App, AffiliateLink, Purchase, Affiliate, Cart, CartItem, Order, OrderItem, DiscountCode, AffiliateCode, AffiliatePartner
from shop_ourapps.models import AffiliatePartner
from .forms import PurchaseForm
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from decimal import Decimal
from django.http import Http404

def our_apps(request):
    apps = App.objects.all()
    return render(request, 'apps/our_apps.html', {'apps': apps})

def shop(request):
    apps = App.objects.filter(is_available_for_purchase=True)
    return render(request, 'apps/shop.html', {'apps': apps})

def app_detail(request, slug):
    app = get_object_or_404(App, slug=slug)
    return render(request, 'apps/app_detail.html', {'app': app})

@login_required
@login_required
def purchase_app(request, slug):
    app = get_object_or_404(App, slug=slug, is_available_for_purchase=True)
    affiliate_code = request.GET.get("ref")

    # Suche nach dem Affiliate-Partner anhand des Codes
    affiliate = None
    if affiliate_code:
        affiliate = Affiliate.objects.filter(code=affiliate_code).first()

    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Kauf speichern
            purchase = Purchase.objects.create(
                user=request.user,
                app=app,
                affiliate=affiliate,
                full_name=data['full_name'],
                email=data['email'],
                address=data['address'],
                zip_code=data['zip_code'],
                city=data['city'],
                country=data['country']
            )

            # E-Mail an Kunden
            send_mail(
                subject=f"Purchase Confirmation: {app.name}",
                message=f"Dear {data['full_name']},\n\nThank you for purchasing {app.name}.",
                recipient_list=[data['email']],
                from_email="joel-digitals@gmx.de"
            )

            # E-Mail an Team
            send_mail(
                subject=f"New Purchase: {app.name}",
                message=f"New order from {data['full_name']} ({data['email']}) for {app.name}\n\nAddress:\n{data['address']}, {data['zip_code']} {data['city']}, {data['country']}",
                recipient_list=["buy.joel-digitals@gmx.de"],
                from_email="joel-digitals@gmx.de"
            )

            return redirect("shop")
    else:
        form = PurchaseForm()

    return render(request, "apps/purchase_form.html", {"app": app, "form": form})



def affiliate_link(request):
    # Generiere einen einzigartigen Affiliate-Link für den Benutzer
    user = request.user
    affiliate_link = f"https://joel-digitals.com/shop/?ref={user.affiliate.code}"
    return render(request, 'apps/affiliate_link.html', {'affiliate_link': affiliate_link})

@login_required
def affiliate_eligibility(request):
    points = 0
    eligible = False
    show_form = False
    input_data = {}

    user = request.user

    if request.method == 'POST':
        input_data = {
            'youtube': int(request.POST.get('youtube', 0)),
            'instagram': int(request.POST.get('instagram', 0)),
            'facebook': int(request.POST.get('facebook', 0)),
            'tiktok': int(request.POST.get('tiktok', 0)),
            'twitter': int(request.POST.get('twitter', 0)),
            'twitch': int(request.POST.get('twitch', 0)),
        }

        points = (
            input_data['youtube'] // 0.5 +
            input_data['instagram'] // 10 +
            input_data['facebook'] // 100 +
            input_data['tiktok'] // 100 +
            input_data['twitter'] // 100 +
            input_data['twitch']
        )

        eligible = points >= 1000
        show_form = eligible and 'name' in request.POST

        if show_form:
            from .models import Affiliate
            affiliate, _ = Affiliate.objects.get_or_create(user=request.user)
            affiliate.name = request.POST.get('name')
            affiliate.address = request.POST.get('address')
            affiliate.email = request.POST.get('email')
            affiliate.save()

            # Links nur bei angegebenem Kanalwert speichern
            links = {}
            for platform in ['youtube', 'instagram', 'facebook', 'tiktok', 'twitter', 'twitch']:
                if input_data[platform] > 0:
                    links[platform] = request.POST.get(f'{platform}_link', '')

            # ✉️ E-Mail senden
            message_lines = [
                f"New Affiliate Application from {affiliate.name}:",
                f"Address: {affiliate.address}",
                f"Email: {affiliate.email}",
                f"Points: {points}",
                f"Eligible: {'Yes' if eligible else 'No'}",
                f"username: {user.username}",
                "",
                "Follower Stats:"
            ]
            for platform, value in input_data.items():
                message_lines.append(f"{platform.capitalize()}: {value}")
                if platform in links:
                    message_lines.append(f"{platform.capitalize()} Link: {links[platform]}")

            message = "\n".join(message_lines)
            subject = f"Affiliate Application from {affiliate.name}"

            # An den Nutzer
            send_mail(
                subject,
                f"Hi {affiliate.name},\n\nthank you for applying!\n\nHere are the submitted details:\n\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                [affiliate.email],
                fail_silently=False
            )

            # An das Marketing-Team
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['joel-digitals@gmx.de'],  # <- Anpassen
                fail_silently=False
            )

            return redirect('affiliate_dashboard')

    return render(request, 'apps/affiliate_eligibility.html', {
        'points': points,
        'eligible': eligible,
        'show_form': show_form,
        'input_data': input_data,
    })

@login_required
def affiliate_dashboard(request):
    try:
        # Berechnung der Affiliate-Statistiken für den eingeloggten Benutzer
        stats = calculate_affiliate_stats(request.user)
        return render(request, "affiliate/dashboard.html", stats)
    except AffiliatePartner.DoesNotExist:
        # Wenn der Benutzer kein Affiliate-Partner ist
        messages.error(request, "You are not yet registered as an Affiliate Partner.")
        return redirect('affiliate_eligibility')  # Weiterleitung zur Registrierung oder Eligibility-Seite


def calculate_affiliate_stats(user):
    try:
        # Versuchen, den Affiliate-Partner für den aktuellen Benutzer zu finden
        partner = AffiliatePartner.objects.get(user=user)
    except AffiliatePartner.DoesNotExist:
        # Kein AffiliatePartner gefunden, Fehler wird bereits oben behandelt
        raise AffiliatePartner.DoesNotExist

    # Beispiel für eine einfache Berechnung (Verkäufe, Einnahmen)
    total_earnings = Decimal('0.00')  # Standardwert für Einnahmen
    total_sales = 0  # Standardwert für Verkäufe

    # Falls der Partner existiert, könnten wir hier weitere Berechnungen vornehmen
    # Beispiel: Berechnung basierend auf Affiliate-Codes, Bestellungen, etc.
    
    # Hier sind Platzhalter, um zu verdeutlichen, dass zusätzliche Logik folgen kann
    # total_sales = berechne_verkaufszahlen(partner)  # z.B. eine Methode, die Verkäufe ermittelt
    # total_earnings = berechne_einnahmen(partner)  # z.B. eine Methode, die die Einnahmen ermittelt

    return {
        "sales": total_sales,
        "earnings": total_earnings,
    }


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(user=request.user)
    total_amount = Decimal('0.0')

    # Berechnung des Bruttobetrags für jedes Item und Sicherstellen, dass es als Decimal behandelt wird
    for item in items:
        item.total_price = Decimal(item.app.price) * Decimal(item.quantity)  # Brutto pro Position

    # Gesamtbrutto (Summe aller Positionen) sicherstellen, dass total_brutto als Decimal behandelt wird
    total_brutto = Decimal(sum(item.total_price for item in items))

    # Netto = Brutto / 1.19 (bei 19 % MwSt)
    total_netto = total_brutto / Decimal('1.19')

    # Steuerbetrag separat berechnen
    total_vat = total_brutto - total_netto

    if request.method == 'POST':
        return redirect('checkout')

    return render(request, 'apps/cart_view.html', {
        'cart': cart,
        'items': items,
        'total_brutto': total_brutto.quantize(Decimal('0.01')),  # Runden auf 2 Dezimalstellen
        'total_netto': total_netto.quantize(Decimal('0.01')),  # Runden auf 2 Dezimalstellen
        'total_vat': total_vat.quantize(Decimal('0.01')),  # Runden auf 2 Dezimalstellen
    })

@login_required
def add_to_cart(request, app_id):
    app = get_object_or_404(App, id=app_id)

    # Wenn der Benutzer noch keinen Warenkorb hat, erstellen wir einen neuen
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Wenn der Artikel bereits im Warenkorb ist, erhöhen wir nur die Menge
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        app=app,
        user=request.user,  # Sicherstellen, dass der Benutzer zugewiesen wird
        defaults={'price': app.price}  # Der Preis wird nur gesetzt, wenn der Artikel neu erstellt wird
    )

    if not created:
        cart_item.quantity += 1  # Erhöhen der Menge, falls der Artikel bereits im Warenkorb ist
        cart_item.save()

    return redirect('cart_view')

@login_required
def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('cart_view')


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    subtotal = sum(item.app.price * item.quantity for item in items)

    discount_amount = 0
    final_total = subtotal
    discount_code_obj = None
    affiliate_code_obj = None

    if request.method == 'POST':
        # Kundendaten aus Formular
        data = request.POST
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        address = data.get('address')
        phone = data.get('phone')
        company_name = data.get('company_name')
        vat_number = data.get('vat_number')
        payment_method = data.get('payment_method')

        affiliate_code_input = data.get('affiliate_code', '').strip()
        discount_code_input = data.get('discount_code', '').strip()

        # Rabattcode prüfen
        if discount_code_input:
            try:
                discount_code_obj = DiscountCode.objects.get(code__iexact=discount_code_input, is_active=True)
                discount_amount = subtotal * (discount_code_obj.percentage / 100)
                final_total = max(0, subtotal - discount_amount)
            except DiscountCode.DoesNotExist:
                messages.error(request, 'Ungültiger Rabattcode.')
                final_total = subtotal

        # Affiliate-Code prüfen
        if affiliate_code_input:
            try:
                affiliate_code_obj = AffiliateCode.objects.get(code__iexact=affiliate_code_input, is_active=True)
            except AffiliateCode.DoesNotExist:
                messages.warning(request, 'Affiliate-Code ist ungültig.')
                affiliate_code_obj = None

        # Bestellung speichern
        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            phone=phone,
            company_name=company_name,
            vat_number=vat_number,
            payment_method=payment_method,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=final_total,
            affiliate_code=affiliate_code_obj,
            discount_code=discount_code_obj,
        )

        # Einzelne Artikel speichern
        for item in items:
            OrderItem.objects.create(
                order=order,
                app=item.app,
                quantity=item.quantity,
                price=item.app.price
            )

        # Rabattcode aktualisieren
        if discount_code_obj:
            discount_code_obj.times_used += 1
            discount_code_obj.save()

        # E-Mails
        if payment_method == 'bank_transfer':
            buyer_subject = 'Ihre Bestellbestätigung - Banküberweisung'
            buyer_message = render_to_string('emails/order_confirmation_bank_transfer.html', {'order': order})
        else:
            buyer_subject = 'Ihre Bestellbestätigung - Rechnung'
            buyer_message = render_to_string('emails/order_confirmation_invoice.html', {'order': order})

        send_mail(buyer_subject, buyer_message, settings.DEFAULT_FROM_EMAIL, [email])

        company_subject = 'Neue Bestellung - Bitte Rechnung senden'
        company_message = render_to_string('emails/order_notification.html', {'order': order})
        send_mail(company_subject, company_message, settings.DEFAULT_FROM_EMAIL, [settings.COMPANY_EMAIL])

        # Warenkorb leeren
        cart.items.all().delete()

        messages.success(request, 'Ihre Bestellung wurde erfolgreich aufgegeben.')
        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'apps/checkout.html', {
        'total': final_total,
        'items': items,
    })


def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'apps/order_confirmation.html', {'order': order})




