from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import App, Purchase, Affiliate, Cart, CartItem, Order, OrderItem, DiscountCode, AffiliateCode, AffiliatePartner, Wallet, Voucher, VoucherOrder
from shop_ourapps.models import AffiliatePartner
from .forms import PurchaseForm, VoucherPurchaseForm
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Sum
import json
from django.utils import timezone
from collections import defaultdict
from django.core.exceptions import ValidationError
from io import BytesIO
from django.http import FileResponse
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from .models import Voucher, VoucherOrder, Wallet
from .forms import VoucherPurchaseForm
import os
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django import forms
from contact.views import is_Sales_Editor
from django.db.models import Q

@login_required
def buy_voucher(request):
    if request.method == 'POST':
        form = VoucherPurchaseForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            recipient_email = form.cleaned_data['recipient_email']
            recipient_name = form.cleaned_data['recipient_name']
            message = form.cleaned_data.get('message', '')
            design = form.cleaned_data.get('design', 'default')

            wallet, _ = Wallet.objects.get_or_create(user=request.user)

            if payment_method == 'wallet':
                if not wallet.deduct(amount):
                    return HttpResponse("Nicht genügend Guthaben im Wallet.", status=400)

                # Direkt Gutschein erstellen
                voucher = Voucher.objects.create(amount=amount, user=request.user)
                VoucherOrder.objects.create(
                    user=request.user,
                    voucher=voucher,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    message=message
                )

                # PDF erstellen und senden
                return generate_voucher_pdf(voucher, recipient_name, recipient_email, message, amount, design)

            elif payment_method == 'paypal':
                # Erstelle eine "Pending"-Order für PayPal
                voucher = Voucher.objects.create(amount=amount, user=request.user, redeemed=True)  # Markiert als "bezahlt" erstmal
                order = VoucherOrder.objects.create(
                    user=request.user,
                    voucher=voucher,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    message=message
                )

                # Weiterleitung zu PayPal
                paypal_url = (
                    f"https://www.paypal.com/cgi-bin/webscr?"
                    f"cmd=_xclick&"
                    f"business=buy.joel-digitals@gmx.de&"
                    f"amount={amount}&"
                    f"currency_code=EUR&"
                    f"item_name=Gutschein #{voucher.code}&"
                    f"invoice={voucher.id}&"
                    f"return={request.build_absolute_uri(reverse('voucher_success', args=[voucher.id]))}&"
                    f"cancel_return={request.build_absolute_uri(reverse('buy_voucher'))}"
                )
                return redirect(paypal_url)

    else:
        form = VoucherPurchaseForm()

    return render(request, 'apps/buy.html', {'form': form})

@login_required
def voucher_success(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id, user=request.user)
    order = get_object_or_404(VoucherOrder, voucher=voucher)

    # PDF generieren und senden
    return generate_voucher_pdf(voucher, order.recipient_name, order.recipient_email, order.message, voucher.amount, 'default')

def generate_voucher_pdf(voucher, recipient_name, recipient_email, message, amount, design):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # === Faltlinien ===
    p.setDash(1, 2)
    p.setStrokeColor(colors.lightgrey)
    p.line(width / 2, 0, width / 2, height)
    p.line(0, height / 2, width, height / 2)
    p.setDash()

    # === Bild ===
    img_path = os.path.join('static', 'gutscheine', f'{design}.jpg')
    if os.path.exists(img_path):
        bg = ImageReader(img_path)
        p.drawImage(bg, width / 2, height / 2, width=width / 2, height=height / 2, preserveAspectRatio=True)

    # === Shopinfos ===
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.black)
    shop_lines = [
        "Joel Digitals",
        "www.joel-digitals.de",
        "joel-digitals@gmx.de",
        "",
        "Wichtiger Hinweis:",
        "Dieser Gutschein ist nur einmal gültig.",
        "Er kann auf www.joel-digitals.onrender.com eingelöst werden.",
        "Keine Barauszahlung möglich.",
    ]
    x, y = 2 * cm, height - 2 * cm
    for line in shop_lines:
        p.drawString(x, y, line)
        y -= 0.5 * cm

    # === Gutscheindaten ===
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, 2 * cm, f"Betrag: {amount:.2f} €")
    p.setFont("Helvetica", 11)
    p.drawString(2 * cm, 1.2 * cm, f"Code: {voucher.code}")
    p.drawString(2 * cm, 0.4 * cm, f"Für: {recipient_name}")

    p.showPage()
    p.save()
    buffer.seek(0)

    # E-Mail senden
    send_mail(
        f"Ihr Gutschein für {recipient_name}",
        f"Hallo {recipient_name},\n\nSie haben einen Gutschein über {amount} € erhalten.\nCode: {voucher.code}",
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
    )

    return FileResponse(buffer, as_attachment=True, filename=f'gutschein_{voucher.code}.pdf')

def redeem_voucher(code, user):
    try:
        voucher = Voucher.objects.get(code=code.upper())
    except Voucher.DoesNotExist:
        raise ValidationError("Dieser Gutscheincode existiert nicht.")

    if voucher.redeemed:
        raise ValidationError("Dieser Gutscheincode wurde bereits eingelöst.")

    # Betrag dem Wallet hinzufügen (angenommen: user.wallet_balance vorhanden)
    user.wallet_balance += voucher.amount
    user.save()

    voucher.redeemed = True
    voucher.redeemed_at = timezone.now()
    voucher.redeemed_by = user
    voucher.save()

def our_apps(request):
    apps = App.objects.filter(is_active=True)  # Nur aktive Apps
    user_groups = request.user.groups.values_list('name', flat=True) if request.user.is_authenticated else []

    return render(request, 'apps/our_apps.html', {
        'apps': apps,
        'user_groups': user_groups,
    })

def shop(request):
    # Nur aktive und kaufbare Apps laden
    apps = App.objects.filter(is_available_for_purchase=True)
    grouped_apps = defaultdict(list)
    group_names = {}

    for app in apps:
        if app.group:
            group_key = app.group.name.strip().lower()
        else:
            # Standardgruppe: erste vier Buchstaben des App-Namens
            group_key = app.name[:4].strip().lower()
        grouped_apps[group_key].append(app)

    # Gruppen alphabetisch sortieren
    grouped_apps = dict(sorted(grouped_apps.items()))

    # Kontext vorbereiten
    context = {
        "grouped_apps": grouped_apps,
        "group_names": group_names,
    }

    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()
        context["wallet_balance"] = wallet.balance if wallet else 0.00

    return render(request, "apps/shop.html", context)

def app_detail(request, slug):
    app = get_object_or_404(App, slug=slug)
    wallet = None  # <--- Fix: Initialisiere wallet standardmäßig mit None
    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()
    return render(request, 'apps/app_detail.html', {
        'app': app,
        'wallet_balance': wallet.balance if wallet else 0.00
    })


@login_required
def wallet_view(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()

    today = now()
    start_of_month = today.replace(day=1)

    try:
        partner = user.affiliatepartner
    except AffiliatePartner.DoesNotExist:
        partner = None

    total_monthly_earnings = Decimal('0.00')
    if partner:
        monthly_orders = Order.objects.filter(
            affiliate_code__partner=partner,
            created_at__gte=start_of_month,
            created_at__lte=today
        )
        total_sales = monthly_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_monthly_earnings = (total_sales * Decimal(partner.commission_percent)) / Decimal('100.00')

    if request.method == "POST":
        # Transfer Earnings
        if 'transfer' in request.POST:
            if wallet.pending_earnings > 0:
                wallet.transfer_to_wallet()
                messages.success(request, "Pending earnings have been transferred to your wallet.")
            else:
                messages.error(request, "No earnings to transfer.")
            return redirect("wallet")

        # Gutscheincode einlösen
        elif 'redeem_code' in request.POST:
            code = request.POST.get("code", "").strip().upper()
            try:
                voucher = Voucher.objects.get(code=code, redeemed=False)
                wallet.balance += voucher.amount
                wallet.save()
                voucher.redeemed = True
                voucher.redeemed_by = user
                voucher.redeemed_at = now()
                voucher.save()
                messages.success(request, f"Gutscheincode '{code}' erfolgreich eingelöst: {voucher.amount} € wurden Ihrem Wallet gutgeschrieben.")
            except Voucher.DoesNotExist:
                messages.error(request, f"Gutscheincode '{code}' ist ungültig oder wurde bereits verwendet.")
            return redirect("wallet")

    return render(request, 'apps/wallet.html', {
        'wallet': wallet,
        'total_monthly_earnings': total_monthly_earnings,
        'pending': wallet.pending_earnings,
        'wallet_balance': wallet.balance if wallet else 0.00
    })

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
        stats = calculate_affiliate_stats(request.user)
        if not stats:
            raise AffiliatePartner.DoesNotExist
        return render(request, "apps/dashboard.html", stats)
    except AffiliatePartner.DoesNotExist:
        messages.error(request, "You are not yet registered as an Affiliate Partner.")
        return redirect('affiliate_eligibility')


def calculate_affiliate_stats(user):
    try:
        affiliate_partner = AffiliatePartner.objects.get(user=user)
        affiliate_code = AffiliateCode.objects.get(partner=affiliate_partner)
    except (AffiliatePartner.DoesNotExist, AffiliateCode.DoesNotExist):
        return {}

    commission_rate = Decimal(affiliate_partner.commission_percent) / Decimal('100')

    orders = Order.objects.filter(affiliate_code=affiliate_code)

    total_sales = sum((order.total_amount for order in orders), Decimal('0.00'))
    earnings = total_sales * commission_rate

    today = now()
    current_year, current_month = today.year, today.month
    monthly_orders = orders.filter(created_at__year=current_year, created_at__month=current_month)
    monthly_sales = sum((order.total_amount for order in monthly_orders), Decimal('0.00'))
    monthly_earnings = monthly_sales * commission_rate

    # Letzte 12 Monate: Umsatz und Verdienst pro Monat
    monthly_data = (
        orders.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(monthly_sales=Sum("total_amount"))
        .order_by("month")
    )

    sales_chart_labels = []
    sales_chart_data = []
    earnings_chart_data = []

    for entry in monthly_data:
        month_label = entry["month"].strftime("%b %Y")
        sales = entry["monthly_sales"] or Decimal('0.00')
        sales_chart_labels.append(month_label)
        sales_chart_data.append(float(sales))
        earnings_chart_data.append(float(sales * commission_rate))

    return {
        "sales": total_sales.quantize(Decimal("0.01")),
        "earnings": earnings.quantize(Decimal("0.01")),
        "monthly_sales": monthly_sales.quantize(Decimal("0.01")),
        "monthly_earnings": monthly_earnings.quantize(Decimal("0.01")),
        "commission_percent": affiliate_partner.commission_percent,
        "affiliate_code": affiliate_code.code,
        "order_count": orders.count(),
        "monthly_order_count": monthly_orders.count(),
        "chart_labels": sales_chart_labels,
        "chart_sales": sales_chart_data,
        "chart_earnings": earnings_chart_data,
    }

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    # Gesamtbrutto mit Decimal-Sicherheit
    total_brutto = sum((item.total_price for item in items), start=Decimal('0.00'))

    # Netto = Brutto / 1.19 (bei 19 % MwSt)
    total_netto = total_brutto / Decimal('1.19') if total_brutto else Decimal('0.00')

    # Steuerbetrag
    total_vat = total_brutto - total_netto

    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()

    if request.method == 'POST':
        return redirect('checkout')

    return render(request, 'apps/cart_view.html', {
        'cart': cart,
        'items': items,
        'total_brutto': total_brutto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_netto': total_netto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_vat': total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'wallet_balance': wallet.balance if wallet else 0.00
    })


def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@require_POST
@login_required
def add_to_cart(request, app_id):
    app = get_object_or_404(App, id=app_id)
    cart = get_user_cart(request.user)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    # Verwende den rabattierten Preis, falls vorhanden
    price_to_use = app.discounted_price

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        cart=cart,
        app=app,
        defaults={'price': price_to_use, 'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('cart_view')


@login_required
@require_POST
def update_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    for item in cart.items.all():
        quantity_key = f'quantity_{item.id}'
        if quantity_key in request.POST:
            try:
                quantity = int(request.POST[quantity_key])
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                else:
                    item.delete()
            except ValueError:
                continue
    return redirect('cart_view')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('cart_view')


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    subtotal = sum(item.app.discounted_price * item.quantity for item in items)

    discount_amount = 0
    final_total = subtotal
    discount_code_obj = None
    affiliate_code_obj = None
    wallet = getattr(request.user, 'wallet', None)

    if request.method == 'POST':
        data = request.POST
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        address = data.get('address')
        zip_code = data.get('zip_code')
        city = data.get('city')
        phone = data.get('phone')
        company_name = data.get('company_name')
        vat_number = data.get('vat_number')
        payment_method = data.get('payment_method')

        affiliate_code_input = data.get('affiliate_code', '').strip()
        discount_code_input = data.get('discount_code', '').strip()

        # Rabattcode prüfen
        if discount_code_input:
            try:
                discount_code_obj = DiscountCode.objects.get(code__iexact=discount_code_input)
                discount_code_obj.update_status()
                if discount_code_obj.is_valid_now():
                    discount_amount = subtotal * (discount_code_obj.percentage / 100)
                    final_total = max(0, subtotal - discount_amount)
                else:
                    messages.error(request, 'Rabattcode ist abgelaufen oder noch nicht gültig.')
                    discount_code_obj = None
            except DiscountCode.DoesNotExist:
                messages.error(request, 'Ungültiger Rabattcode.')

        # Affiliate-Code prüfen
        if affiliate_code_input:
            try:
                affiliate_code_obj = AffiliateCode.objects.get(code__iexact=affiliate_code_input, is_active=True)
            except AffiliateCode.DoesNotExist:
                messages.warning(request, 'Affiliate-Code ist ungültig.')

        # Wallet prüfen
        if payment_method == 'wallet':
            if not wallet or not wallet.has_funds(final_total):
                messages.error(request, 'Nicht genügend Guthaben im Wallet.')
                return redirect('checkout')

        # Order erstellen
        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            zip_code=zip_code,
            city=city,
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

        for item in items:
            OrderItem.objects.create(
                order=order,
                app=item.app,
                quantity=item.quantity,
                price=item.app.discounted_price  # rabattierte Preis verwenden
            )

        if discount_code_obj:
            discount_code_obj.times_used += 1
            discount_code_obj.save()

        # Wallet-Abzug und Abschluss
        if payment_method == 'wallet':
            wallet.deduct(final_total)
            messages.success(request, 'Ihre Bestellung wurde erfolgreich aufgegeben.')
            cart.items.all().delete()
            
            send_order_emails(order, request)  # E-Mails verschicken
            
            return redirect('order_confirmation', order_id=order.id)

        if payment_method == 'paypal':
            send_order_emails(order, request)  # E-Mails verschicken vor Weiterleitung
            return redirect(reverse('paypal_checkout', args=[order.id]))

    context = {
        'items': items,
        'subtotal': subtotal,  # <--- Originalpreis ohne Rabatt
        'total': final_total,  # <--- Endpreis nach Rabatt
        'discount_amount': discount_amount,
        'wallet_balance': wallet.balance if wallet else 0,
        'now': timezone.now(),
    }
    return render(request, 'apps/checkout.html', context)


def send_order_emails(order, request):
    """
    Versand der Mails an Kunde und Admin mit Vorlagen.
    """

    # Mail an Kunde
    subject_customer = 'Bestellbestätigung – Joel Digitals'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [order.email]

    context = {
        'order': order,
        'now': timezone.now(),
    }

    html_content = render_to_string('emails/order_customer_info.html', context)
    text_content = render_to_string('emails/order_customer_info.txt', context)

    msg = EmailMultiAlternatives(subject_customer, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    # Mail an Admin
    subject_admin = f'Neue Bestellung #{order.id} von {order.first_name} {order.last_name}'
    to_admin = ['buy.joel-digitals@gmx.de']
    admin_context = {
        'order': order,
        'order_url': request.build_absolute_uri(reverse('order_admin')),
    }
    admin_html = render_to_string('emails/order_admin_notification.html', admin_context)
    admin_text = render_to_string('emails/order_admin_notification.txt', admin_context)

    admin_msg = EmailMultiAlternatives(subject_admin, admin_text, from_email, to_admin)
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()

@login_required
def paypal_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='paypal')
    paypal_url = (
        f"https://www.paypal.com/cgi-bin/webscr?"
        f"cmd=_xclick&"
        f"business=buy.joel-digitals@gmx.de&"
        f"amount={order.total_amount}&"
        f"currency_code=EUR&"
        f"item_name=Bestellung #{order.id}&"
        f"invoice={order.id}&"
        f"return={request.build_absolute_uri(reverse('order_confirmation', args=[order.id]))}&"
        f"cancel_return={request.build_absolute_uri(reverse('checkout'))}"
    )
    return redirect(paypal_url)

@csrf_exempt
@login_required
def paypal_confirm(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        total = Decimal(data.get('total'))

        # Hier kannst du die Bestellung finalisieren
        order = Order.objects.create(
            user=request.user,
            payment_method='paypal',
            total_amount=total,
            # ... weitere Felder
        )

        return JsonResponse({'status': 'success', 'order_id': order.id})

@login_required
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'apps/order_confirmation.html', {'order': order})

@require_POST
@login_required
def validate_codes(request):
    data = json.loads(request.body)
    subtotal = sum(item.price * item.quantity for item in request.user.cart.items.all)
    discount = 0

    try:
        discount_code = DiscountCode.objects.get(code__iexact=data.get("discount_code", ""))
        discount_code.update_status()
        if discount_code.is_valid_now():
            discount = subtotal * (discount_code.percentage / 100)
        else:
            return JsonResponse({"valid": False, "message": "Rabattcode ist ungültig oder abgelaufen."})
    except DiscountCode.DoesNotExist:
        if data.get("discount_code"):
            return JsonResponse({"valid": False, "message": "Rabattcode nicht gefunden."})

    total = max(0, subtotal - discount)
    return JsonResponse({
        "valid": True,
        "new_total": f"{total:.2f}",
        "discount": f"{discount:.2f}"
    })

def more_informations(request, slug):
    app = get_object_or_404(App, slug=slug)
    return render(request, 'apps/app_infos.html', {'app': app})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'apps/my_orders.html', {'orders': orders})


class SendAccessMailForm(forms.Form):
    MESSAGE_CHOICES = [
        ('welcome', 'Welcome Message'),
        ('registration', 'Registration Code'),
        ('apps_info', 'Apps & Codes Info'),
    ]

    message_type = forms.ChoiceField(
        choices=MESSAGE_CHOICES,
        label="Select Message Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    registration_codes = forms.CharField(
        required=False,
        label="Registration Codes (AppName:Code, comma-separated)",
        widget=forms.Textarea(attrs={
            "placeholder": "AppName1:Code1, AppName2:Code2",
            "rows": 4,
            "class": "form-control"
        })
    )

    suggested_apps = forms.MultipleChoiceField(
        required=False,
        label="Empfohlene Apps",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Vorschläge (kann auch aus DB stammen)
        self.fields['suggested_apps'].choices = [
            ('JDS Management', 'JDS Management – Easy, smart and fast.'),
        ]

    def extract_app_names(self):
        apps = []
        raw = self.cleaned_data.get("registration_codes", "")
        for part in raw.split(','):
            if ':' in part:
                app, _ = part.split(':', 1)
                apps.append(app.strip())
        return apps

@user_passes_test(is_Sales_Editor)
def order_admin(request):
    tab = request.GET.get('tab', 'pending')
    query = request.GET.get('q', '').strip()

    if tab == 'pending':
        orders = Order.objects.filter(status='pending')
    elif tab == 'completed':
        orders = Order.objects.filter(status='completed')
    elif tab == 'returns':
        orders = Order.objects.filter(status__in=['cancelled', 'return', 'shipped'])
    elif tab == 'shipping':
        orders = Order.objects.filter(status__in=['in_delivery', 'delivered'])
    elif tab == 'finished':
        orders = Order.objects.filter(status__in=['finished'])
    else:
        orders = Order.objects.all() 

    if query:
        filters &= (
            Q(id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )


    if request.method == 'POST':
        form = SendAccessMailForm(request.POST)
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')

        try:
            order = Order.objects.get(id=order_id)

            # Statusaktualisierung (unabhängig vom E-Mail-Versand)
            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                order.save()
                messages.success(request, f"Bestellung #{order.id}: Status geändert von '{old_status}' auf '{new_status}'.")
                return redirect(f"{request.path}?tab={new_status}")

            if form.is_valid():
                message_type = form.cleaned_data["message_type"]
                registration_codes_raw = form.cleaned_data["registration_codes"]
                suggested_ids = form.cleaned_data.get("suggested_apps", [])

                # Registrierungscodes parsen
                codes = {}
                for part in registration_codes_raw.split(','):
                    if ':' in part:
                        app, code = part.split(':', 1)
                        codes[app.strip()] = code.strip()

                # Vorschläge aus IDs aufbauen
                suggestion_map = {
                    'JDS Management': {
                        'title': 'JDS Management',
                        'description': 'Manage fast, easy und ',
                        'url': 'https://www.joel-digitals.de/our-apps/ManagementApp/',
                        'btn_text': 'Jetzt entdecken',
                    },
                    'editorx': {
                        'title': 'Editor X',
                        'description': 'Ein leistungsstarker Editor für Code & Markdown.',
                        'url': 'https://joel-digitals.de/store/editorx',
                        'btn_text': 'Jetzt ansehen',
                    },
                    'weatherai': {
                        'title': 'Weather AI',
                        'description': 'Intelligente Wettervorhersage mit KI.',
                        'url': 'https://joel-digitals.de/store/weatherai',
                        'btn_text': 'Mehr erfahren',
                    },
                }

                suggestions = [suggestion_map[sid] for sid in suggested_ids if sid in suggestion_map]

                context = {
                    'order': order,
                    'codes': codes,
                    'apps': codes.keys(),
                    'message_type': message_type,
                    'suggestions': suggestions,
                    'now': timezone.now(),
                }

                # E-Mail-Inhalt generieren
                html_content = render_to_string(f'emails/{message_type}.html', context)
                subject_map = {
                    'welcome': 'Willkommensnachricht zu Ihrer Bestellung',
                    'registration': 'Ihre Registrierungscodes',
                    'apps_info': 'Informationen zu Ihren Apps und Codes',
                }
                subject = subject_map.get(message_type, 'Ihre Zugangsdaten')

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body="Bitte verwenden Sie ein HTML-fähiges E-Mail-Programm.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[order.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                messages.success(request, f"E-Mail '{subject}' an {order.email} gesendet.")

        except Order.DoesNotExist:
            messages.error(request, "Bestellung nicht gefunden.")
        except Exception as e:
            messages.error(request, f"Fehler beim Verarbeiten: {e}")

        return redirect(f"{request.path}?tab={tab}")

    mail_form = SendAccessMailForm()

    return render(request, 'apps/order_admin.html', {
        'orders': orders,
        'tab': tab,
        'mail_form': mail_form,
    })