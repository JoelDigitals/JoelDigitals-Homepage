import requests
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Diese Datei ist GEGEN DEN ECHTEN JDS-MANAGEMENT-CODE VERIFIZIERT (main/api_v2.py
# im JDS-Management-Repo, Stand 2026-07-19) - nicht mehr spekulativ. Wichtige
# reale Eigenheiten der API, die hier beruecksichtigt werden:
#   - Erfolgs-Antworten sind IMMER als {"data": {...}} verpackt (siehe _unwrap).
#   - /api/v2/products/<id>/ und /api/v2/customers/<id>/ werden per INTERNER
#     NUMERISCHER ID adressiert, NICHT per product_number/customer_number-String.
#   - Kunden: POST akzeptiert first_name/last_name/email/phone_number/address/
#     customer_type. PATCH akzeptiert NUR first_name/last_name/email/phone_number/
#     customer_type (kein address/company/vat_number!). Es gibt KEIN Dedup per
#     E-Mail serverseitig - ein POST legt IMMER einen neuen Kunden an, deshalb
#     merken wir uns die zurueckgegebene ID lokal und nutzen ab dann PATCH.
#   - Es gibt KEIN /api/v2/orders/. Bestellungen werden stattdessen als Einnahme
#     (/api/v2/incomes/) verbucht - ebenfalls ohne serverseitige Deduplizierung,
#     daher lokale Sperre ueber Order.jds_synced_at (siehe push_order).
# ─────────────────────────────────────────────────────────────────────────────


def get_api_headers():
    return {
        "X-Team-Code": settings.JDS_TEAM_CODE,
        "Authorization": f"Bearer {settings.JDS_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _unwrap(data):
    """Erfolgs-Antworten von JDS Management sind immer {"data": ...} verpackt."""
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def fetch_products():
    url = f"{settings.JDS_API_BASE_URL}/api/v2/products/"
    try:
        resp = requests.get(url, headers=get_api_headers(), timeout=15)
        resp.raise_for_status()
        data = _unwrap(resp.json())

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("results", "products", "items"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []
    except requests.RequestException as e:
        logger.error(f"JDS API fetch_products failed: {e}")
        return []


def sync_stock():
    """
    Holt alle Produkte aus JDS Management und gleicht lokalen Bestand ab.
    Merkt sich zusaetzlich die interne JDS-Produkt-ID (App.jds_product_id) -
    die wird fuer update_product_stock() gebraucht, da die Detail-Route dort
    per numerischer ID adressiert wird, nicht per product_number.
    """
    from ..models import App, Package, PackageApp
    from django.db.models import Min

    products = fetch_products()
    if not products:
        logger.warning("JDS API returned no products, stock sync skipped")
        return 0

    updated = 0
    for p in products:
        if not isinstance(p, dict):
            continue

        product_number = str(p.get("product_number") or "")
        stock = p.get("stock", 0)
        jds_id = p.get("id")

        app = None
        if product_number:
            app = App.objects.filter(product_number=product_number).first()
        if not app:
            name = p.get("name", "")
            if name:
                matches = App.objects.filter(name__iexact=name)
                if matches.count() == 1:
                    app = matches.first()

        if app:
            update_fields = []
            new_stock = int(float(stock))
            if app.stock != new_stock:
                app.stock = new_stock
                update_fields.append("stock")
            if jds_id and str(app.jds_product_id) != str(jds_id):
                app.jds_product_id = str(jds_id)
                update_fields.append("jds_product_id")
            if update_fields:
                app.save(update_fields=update_fields)
            updated += 1

    # Package.stock aus dem Minimum der enthaltenen Apps aktualisieren
    for pkg in Package.objects.filter(packageapp__isnull=False).distinct():
        min_stock = PackageApp.objects.filter(package=pkg).aggregate(Min('app__stock'))['app__stock__min']
        pkg.stock = min_stock or 0
        pkg.save(update_fields=["stock"])

    return updated


def update_product_stock(app, new_stock):
    """
    Sendet den aktualisierten Lagerbestand an die JDS Management API
    (PATCH /api/v2/products/<jds_product_id>/). Braucht die von sync_stock()
    lokal gemerkte interne JDS-ID - die Route akzeptiert KEINE product_number-
    Strings. Ohne bekannte jds_product_id wird der Aufruf uebersprungen (statt
    mit einer garantiert falschen URL zu 404en) - der naechste sync_stock()-Lauf
    (Cron) liefert sie nach.
    """
    if not app.jds_product_id:
        logger.warning(
            f"JDS API update_stock uebersprungen fuer '{app.product_number or app.name}': "
            f"keine jds_product_id bekannt (sync_stock() muss zuerst einmal laufen)."
        )
        return False

    url = f"{settings.JDS_API_BASE_URL}/api/v2/products/{app.jds_product_id}/"
    try:
        resp = requests.patch(url, headers=get_api_headers(), json={"stock": new_stock}, timeout=15)
        resp.raise_for_status()
        logger.info(f"JDS API stock updated for {app.product_number} (jds id {app.jds_product_id}): {new_stock}")
        return True
    except requests.RequestException as e:
        logger.error(f"JDS API update_stock failed for {app.product_number} (jds id {app.jds_product_id}): {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# KUNDEN-SYNC (Homepage → JDS Management)
#
# Jeder Kunde mit shop_ourapps.CustomerInfo (also jeder, der je Kontaktdaten im
# Checkout hinterlegt hat) wird hier synchronisiert - unabhaengig davon, ob er
# schon eine bezahlte Bestellung abgeschlossen hat (siehe sync_customer_info).
# push_order() (pro Order) verwendet, falls vorhanden, dieselbe interne ID,
# damit in JDS Management kein doppelter Kundendatensatz entsteht - es gibt
# dort KEIN serverseitiges Dedup per E-Mail.
# ─────────────────────────────────────────────────────────────────────────────

def _customer_create_payload(*, email, first_name, last_name, phone, address, zip_code, city):
    """Felder, die POST /api/v2/customers/ akzeptiert. company_name/vat_number
    werden dort NICHT entgegengenommen (die haengen serverseitig an einer
    separaten Company-Verknuepfung, die diese Route nicht setzt)."""
    full_address = f"{address}, {zip_code} {city}".strip(", ") if (address or zip_code or city) else ""
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone,
        "address": full_address,
        "customer_type": "Privatkunde",
    }


def _customer_update_payload(*, email, first_name, last_name, phone):
    """PATCH /api/v2/customers/<id>/ akzeptiert NUR diese Felder - kein
    address/company_name/vat_number (serverseitige Einschraenkung)."""
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone,
    }


def _create_or_update_customer(*, email, first_name, last_name, phone, address, zip_code, city, existing_customer_id=None):
    """Legt einen neuen Kunden an (POST /api/v2/customers/) oder aktualisiert
    einen bestehenden (PATCH /api/v2/customers/<id>/, falls existing_customer_id
    gesetzt ist). Gibt (customer_id, customer_number, error_message) zurueck -
    customer_id ist die interne numerische ID (fuer spaetere PATCH-Aufrufe),
    customer_number die menschenlesbare Kundennummer (z.B. "C20260001")."""
    if existing_customer_id:
        url = f"{settings.JDS_API_BASE_URL}/api/v2/customers/{existing_customer_id}/"
        payload = _customer_update_payload(email=email, first_name=first_name, last_name=last_name, phone=phone)
        method = requests.patch
    else:
        url = f"{settings.JDS_API_BASE_URL}/api/v2/customers/"
        payload = _customer_create_payload(
            email=email, first_name=first_name, last_name=last_name, phone=phone,
            address=address, zip_code=zip_code, city=city,
        )
        method = requests.post

    try:
        resp = method(url, headers=get_api_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        customer = _unwrap(resp.json())
        customer_id = customer.get("id") or existing_customer_id
        customer_number = customer.get("customer_number") or ""
        if not customer_id:
            return None, "", f"Keine Kunden-ID in der API-Antwort: {customer}"
        return str(customer_id), customer_number, ""
    except requests.RequestException as e:
        return existing_customer_id, "", str(e)


def find_or_create_customer(order):
    """
    Sucht/legt den Kunden der Bestellung in JDS Management an. Verwendet
    zuerst eine bereits bekannte Kunden-ID (Order selbst oder die CustomerInfo
    des bestellenden Users), damit pro Kunde nur EIN JDS-Management-Datensatz
    entsteht. Gibt die interne Kunden-ID zurueck oder None bei Fehler.
    """
    existing_id = order.jds_customer_id or None
    if not existing_id and order.user_id:
        try:
            existing_id = order.user.customer_info.jds_customer_id or None
        except Exception:
            existing_id = None

    customer_id, _customer_number, error = _create_or_update_customer(
        email=order.email, first_name=order.first_name, last_name=order.last_name,
        phone=order.phone, address=order.address, zip_code=order.zip_code, city=order.city,
        existing_customer_id=existing_id,
    )
    if error:
        logger.error(f"JDS API find_or_create_customer failed for Order {order.id}: {error}")
    return customer_id


def sync_customer_info(customer_info):
    """
    Legt einen Kunden bei Erstkontakt (erste ausgefuellte Checkout-Kontaktdaten)
    in JDS Management an bzw. aktualisiert seine Daten dort, wenn sich
    CustomerInfo aendert - unabhaengig davon, ob er je eine bezahlte Bestellung
    abgeschlossen hat. Aktualisiert CustomerInfo.jds_customer_id/
    jds_customer_number/jds_synced_at/jds_sync_error. Best-effort, blockiert
    den Checkout/das Speichern nie.

    Hinweis Firma/USt-IdNr.: die JDS-Management-API nimmt company_name/
    vat_number ueber diese Route (noch) nicht entgegen - diese Felder werden
    lokal weiter gespeichert, aber aktuell NICHT nach JDS Management uebertragen.
    """
    customer_id, customer_number, error = _create_or_update_customer(
        email=customer_info.email, first_name=customer_info.first_name, last_name=customer_info.last_name,
        phone=customer_info.phone, address=customer_info.address, zip_code=customer_info.zip_code,
        city=customer_info.city, existing_customer_id=customer_info.jds_customer_id or None,
    )

    if customer_id:
        customer_info.jds_customer_id = customer_id
        if customer_number:
            customer_info.jds_customer_number = customer_number
        customer_info.jds_synced_at = timezone.now()
    customer_info.jds_sync_error = error
    customer_info.save(update_fields=["jds_customer_id", "jds_customer_number", "jds_synced_at", "jds_sync_error"])

    if error:
        logger.error(f"JDS API sync_customer_info failed for user {customer_info.user_id}: {error}")
    return customer_id


def sync_pending_customers(limit=50):
    """
    Batch-Nachzuegler-Sync fuer den Cron (siehe JoelDigitalsApp.cron.push_check):
    Kunden, die noch nie erfolgreich synct wurden oder deren letzter Sync-
    Versuch fehlgeschlagen ist, werden hier nachtraeglich uebertragen -
    verhindert, dass ein einzelner API-Ausfall einen Kunden dauerhaft ohne
    Kundennummer laesst. Deckt auch alle VOR Einfuehrung dieses Features
    bereits vorhandenen Kunden ab (die haben ebenfalls kein jds_customer_id).
    """
    from ..models import CustomerInfo
    from django.db.models import Q

    candidates = CustomerInfo.objects.filter(
        Q(jds_customer_id__isnull=True) | Q(jds_customer_id="") | ~Q(jds_sync_error="")
    ).exclude(email="")[:limit]

    synced = []
    for customer_info in candidates:
        if sync_customer_info(customer_info):
            synced.append(customer_info.user_id)
    return synced


# ─────────────────────────────────────────────────────────────────────────────
# BESTELLUNGEN → EINNAHMEN (Homepage → JDS Management)
#
# JDS Management hat keinen allgemeinen "Order"-Endpunkt - Homepage-Bestellungen
# werden stattdessen als Einnahme gebucht (POST /api/v2/incomes/), mit
# Bestellnummer + "Homepage"-Vermerk im Freitext (description), da die
# Einnahmen-API keine externe Referenznummer/Kategorie-Strings/Kundenverknuepfung
# kennt. KEINE serverseitige Deduplizierung - deshalb lokale Sperre ueber
# Order.jds_synced_at, damit ein wiederholter Aufruf (z.B. per Admin-Aktion)
# nicht zweimal dieselbe Einnahme anlegt.
# ─────────────────────────────────────────────────────────────────────────────

_ZAHLUNGSMETHODE_MAP = {
    "überweisung": "bank",
    "lastschrift": "bank",
    "wallet": "sonstig",
    "stripe": "karte",
    "paypal": "paypal",
    "manual": "sonstig",
}


def push_order(order, force=False):
    """
    Legt den Kunden (falls noetig) in JDS Management an/aktualisiert ihn und
    verbucht die Bestellung als Einnahme, damit sie dort in der Buchhaltung
    sichtbar ist. Aktualisiert Order.jds_customer_id / jds_synced_at /
    jds_sync_error zur Nachverfolgung im Admin. Wird best-effort aufgerufen
    (z.B. wenn eine Order 'Paid' wird) und darf den Checkout niemals blockieren.

    force=True erzwingt eine erneute Buchung selbst wenn schon erfolgreich
    synct (nur fuer bewusste manuelle Korrekturen - erzeugt sonst eine zweite
    Einnahme, da /api/v2/incomes/ nicht dedupliziert).
    """
    if order.jds_synced_at and not order.jds_sync_error and not force:
        logger.info(f"JDS API: Order {order.id} bereits als Einnahme verbucht, ueberspringe (kein Dedup serverseitig).")
        return True

    customer_id = order.jds_customer_id or find_or_create_customer(order)
    if not customer_id:
        order.jds_sync_error = "Kunde konnte nicht in JDS Management angelegt/gefunden werden."
        order.save(update_fields=["jds_sync_error"])
        return False

    item_lines = "; ".join(
        f"{item.quantity}x {item.get_name()}" for item in order.items.all()
    ) or "—"
    zahlungsmethode = _ZAHLUNGSMETHODE_MAP.get((order.payment_method or "").lower(), "sonstig")

    url = f"{settings.JDS_API_BASE_URL}/api/v2/incomes/"
    payload = {
        "amount": str(order.total_amount),
        "date": order.created_at.date().isoformat(),
        "description": (
            f"Homepage-Bestellung #{order.id} - Kunde: {order.first_name} {order.last_name} "
            f"({order.email}) - {item_lines}"
        ),
        "invoice_number": f"JD-{order.id}",
        "zahlungsmethode": zahlungsmethode,
    }
    try:
        resp = requests.post(url, headers=get_api_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        income = _unwrap(resp.json())
        order.jds_customer_id = customer_id
        order.jds_synced_at = timezone.now()
        order.jds_sync_error = ""
        order.save(update_fields=["jds_customer_id", "jds_synced_at", "jds_sync_error"])
        logger.info(f"JDS API: Order {order.id} als Einnahme #{income.get('id')} verbucht (Kunde {customer_id})")
        return True
    except requests.RequestException as e:
        order.jds_customer_id = customer_id
        order.jds_sync_error = str(e)
        order.save(update_fields=["jds_customer_id", "jds_sync_error"])
        logger.error(f"JDS API push_order failed for Order {order.id}: {e}")
        return False
