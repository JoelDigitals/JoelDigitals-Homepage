from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from .models import App, AffiliateLink, Purchase, Affiliate, Cart, CartItem, Order, OrderItem, DiscountCode, AffiliateCode, AffiliatePartner, Wallet, Voucher, VoucherOrder
from shop_ourapps.models import AffiliatePartner
from .forms import PurchaseForm, VoucherPurchaseForm
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from decimal import Decimal, ROUND_HALF_UP
from django.http import Http404, JsonResponse
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
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from .models import Voucher, VoucherOrder, Wallet
from .forms import VoucherPurchaseForm
import os
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.core.exceptions import ValidationError

from reportlab.lib.utils import ImageReader, simpleSplit

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
            if payment_method == 'wallet' and not wallet.deduct(amount):
                return HttpResponse("Nicht genügend Guthaben im Wallet.", status=400)

            voucher = Voucher.objects.create(amount=amount, user=request.user)
            VoucherOrder.objects.create(
                user=request.user,
                voucher=voucher,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                message=message
            )

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=landscape(A4))
            width, height = landscape(A4)
            
            # === Faltlinien ===
            p.setDash(1, 2)
            p.setStrokeColor(colors.lightgrey)
            # Vertikal halbieren
            p.line(width / 2, 0, width / 2, height)
            # Horizontal halbieren
            p.line(0, height / 2, width, height / 2)
            p.setDash()  # Reset

            # === Bild oben rechts (1/4 Seite) ===
            img_path = os.path.join('static', 'gutscheine', f'{design}.jpg')
            if os.path.exists(img_path):
                bg = ImageReader(img_path)
                p.drawImage(bg, width / 2, height / 2, width=width / 2, height=height / 2, preserveAspectRatio=True)
            else:
                p.setFillColor(colors.white)
                p.rect(0, 0, width, height, fill=True, stroke=0)

            # === Shopinfos oben links ===
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
            x, y = cm, height - 2 * cm
            for line in shop_lines:
                p.drawString(x, y, line)
                y -= 0.5 * cm

            # === Logo UNTER Shopinfos ===
            logo_path = os.path.join('static', 'logo.png')
            if os.path.exists(logo_path):
                logo = ImageReader(logo_path)
                p.drawImage(logo, cm, y - 3.5 * cm, width=4 * cm, preserveAspectRatio=True, mask='auto')

            p.saveState()

            # Ursprung auf linken unteren Rand des Bildbereichs (oben rechts auf der Seite)
            p.translate(width / 2, height / 2)
            p.rotate(180)
            
            # Textbereich: Breite und maximale Höhe (halbe Bildhöhe)
            box_width = width / 2 - 2 * cm
            box_height = (height / 2) / 2 - 1 * cm  # halbe Bildhöhe minus etwas Rand
            
            x_text = cm
            y_start = cm  # beginnt unten
            
            # Textstil
            style = getSampleStyleSheet()["Normal"]
            style.fontName = "Helvetica"
            style.fontSize = 11
            style.leading = 13
            style.textColor = colors.darkblue
            
            # Text vorbereiten (manueller Umbruch für ReportLab Canvas)
            wrapped_lines = simpleSplit(message, style.fontName, style.fontSize, box_width)
            
            # Nur so viele Zeilen wie in box_height passen
            max_lines = int(box_height // style.leading)
            visible_lines = wrapped_lines[:max_lines]
            
            # Überschrift
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.black)
            p.drawString(x_text, y_start + style.leading * (len(visible_lines) + 1), "Persönliche Nachricht:")
            
            # Nachricht selbst
            p.setFont("Helvetica", 11)
            p.setFillColor(colors.darkblue)
            textobject = p.beginText(x_text, y_start)
            for line in visible_lines:
                textobject.textLine(line)
            p.drawText(textobject)
            
            p.restoreState()

            # === Gutscheindaten – UNTEN RECHTS, unterhalb des Bildes, auf dem Kopf ===
            p.saveState()

            # Position berechnen: rechte Hälfte (x), unterhalb des Bildes (y)
            block_margin_x = 2 * cm  # Abstand vom rechten Rand nach innen
            block_margin_y = 2 * cm  # Abstand vom unteren Rand nach oben

            # Wir platzieren den Ursprung am unteren rechten Viertel der Seite
            p.translate(width / 2 + block_margin_x + 10 * cm, block_margin_y)
            p.rotate(180)  # Auf den Kopf drehen

            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.black)

            # Koordinaten beginnen gedreht von hier
            x_info = 0
            y_info = 0

            p.drawString(x_info, y_info, f"Amount: {amount:.2f} €")
            p.setFont("Helvetica", 11)
            p.drawString(x_info, y_info - 1.0 * cm, f"COde: {voucher.code}")
            p.drawString(x_info, y_info - 2.0 * cm, f"For: {recipient_name}")
            p.drawString(x_info, y_info - 3.0 * cm, f"Date: {now().strftime('%d.%m.%Y')}")

            p.restoreState()

            


            p.showPage()
            p.save()

            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=f'gutschein_{voucher.code}.pdf')
    else:
        form = VoucherPurchaseForm()

    return render(request, 'apps/buy.html', {'form': form})




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
    return render(request, 'apps/app_detail.html', {'app': app})

@login_required
def wallet_view(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)

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

    if request.method == 'POST':
        return redirect('checkout')

    return render(request, 'apps/cart_view.html', {
        'cart': cart,
        'items': items,
        'total_brutto': total_brutto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_netto': total_netto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_vat': total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
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

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        cart=cart,
        app=app,
        defaults={'price': app.price, 'quantity': quantity}
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
    subtotal = sum(item.app.price * item.quantity for item in items)

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
        phone = data.get('phone')
        company_name = data.get('company_name')
        vat_number = data.get('vat_number')
        payment_method = data.get('payment_method')

        affiliate_code_input = data.get('affiliate_code', '').strip()
        discount_code_input = data.get('discount_code', '').strip()

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

        if affiliate_code_input:
            try:
                affiliate_code_obj = AffiliateCode.objects.get(code__iexact=affiliate_code_input, is_active=True)
            except AffiliateCode.DoesNotExist:
                messages.warning(request, 'Affiliate-Code ist ungültig.')

        if payment_method == 'wallet':
            if not wallet or not wallet.has_funds(final_total):
                messages.error(request, 'Nicht genügend Guthaben im Wallet.')
                return redirect('checkout')

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

        for item in items:
            OrderItem.objects.create(order=order, app=item.app, quantity=item.quantity, price=item.app.price)

        if discount_code_obj:
            discount_code_obj.times_used += 1
            discount_code_obj.save()

        if payment_method == 'wallet':
            wallet.deduct(final_total)

        if payment_method == 'bank_transfer':
            buyer_subject = 'Ihre Bestellbestätigung - Banküberweisung'
            buyer_message = render_to_string('emails/order_confirmation_bank_transfer.html', {'order': order})
        elif payment_method == 'wallet':
            buyer_subject = 'Ihre Bestellbestätigung - Wallet'
            buyer_message = render_to_string('emails/order_confirmation_wallet.html', {'order': order})
        else:
            buyer_subject = 'Ihre Bestellbestätigung - Rechnung'
            buyer_message = render_to_string('emails/order_confirmation_invoice.html', {'order': order})

        send_mail(buyer_subject, buyer_message, settings.DEFAULT_FROM_EMAIL, [email])
        company_subject = 'Neue Bestellung - Bitte Rechnung senden'
        company_message = render_to_string('emails/order_notification.html', {'order': order})
        send_mail(company_subject, company_message, settings.DEFAULT_FROM_EMAIL, [settings.COMPANY_EMAIL])

        cart.items.all().delete()
        messages.success(request, 'Ihre Bestellung wurde erfolgreich aufgegeben.')
        return redirect('order_confirmation')  # oder eine Bestätigungsseite

    context = {
        'items': items,
        'total': final_total,
        'discount_amount': discount_amount,
        'wallet_balance': wallet.balance if wallet else 0,
        'now': timezone.now(),
    }
    return render(request, 'apps/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'apps/order_confirmation.html', {'order': order})

@require_POST
@login_required
def validate_codes(request):
    data = json.loads(request.body)
    subtotal = sum(item.app.price * item.quantity for item in request.user.cart.items.all())
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


