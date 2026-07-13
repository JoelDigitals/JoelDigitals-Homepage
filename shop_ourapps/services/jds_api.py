import requests
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_api_headers():
    return {
        "X-Team-Code": settings.JDS_TEAM_CODE,
        "Authorization": f"Bearer {settings.JDS_API_TOKEN}",
        "Content-Type": "application/json",
    }


def fetch_products():
    url = f"{settings.JDS_API_BASE_URL}/api/v2/products/"
    try:
        resp = requests.get(url, headers=get_api_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("results", "data", "products", "items"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []
    except requests.RequestException as e:
        logger.error(f"JDS API fetch_products failed: {e}")
        return []


def sync_stock():
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

        product_number = str(p.get("product_number") or p.get("id") or "")
        stock = p.get("stock", 0)
        if not product_number:
            continue

        try:
            app = App.objects.get(product_number=product_number)
            app.stock = int(float(stock))
            app.save(update_fields=["stock"])
            updated += 1
        except App.DoesNotExist:
            name = p.get("name", "")
            if name:
                try:
                    app = App.objects.get(name__iexact=name)
                    app.stock = int(float(stock))
                    app.save(update_fields=["stock"])
                    updated += 1
                except (App.DoesNotExist, App.MultipleObjectsReturned):
                    pass

    # Package.stock aus dem Minimum der enthaltenen Apps aktualisieren
    for pkg in Package.objects.filter(packageapp__isnull=False).distinct():
        min_stock = PackageApp.objects.filter(package=pkg).aggregate(Min('app__stock'))['app__stock__min']
        pkg.stock = min_stock or 0
        pkg.save(update_fields=["stock"])

    return updated


def update_product_stock(product_number, new_stock):
    """
    Sendet den aktualisierten Lagerbestand an die JDS Management API.
    Wird nach erfolgreichem Kaufs aufgerufen, damit das Warenwirtschaftssystem
    den reduzierten Bestand kennt.
    """
    url = f"{settings.JDS_API_BASE_URL}/api/v2/products/{product_number}/"
    try:
        resp = requests.patch(url, headers=get_api_headers(), json={"stock": new_stock}, timeout=15)
        resp.raise_for_status()
        logger.info(f"JDS API stock updated for {product_number}: {new_stock}")
        return True
    except requests.RequestException as e:
        logger.error(f"JDS API update_stock failed for {product_number}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# KUNDEN- & BESTELL-SYNC (Homepage → JDS Management)
#
# WICHTIG: /api/v2/customers/ und /api/v2/orders/ folgen hier nur der gleichen
# Namenskonvention wie das bereits produktiv genutzte /api/v2/products/.
# Das eigentliche Feld-Mapping (customer_number, order-Felder, Antwortformat)
# ist NICHT verifiziert - bitte gegen die echte JDS-Management-API testen und
# bei Abweichungen die Feldnamen unten anpassen. Schlaegt der Sync fehl, wird
# das nur geloggt/auf der Order vermerkt - der Checkout selbst wird dadurch
# nicht blockiert.
# ─────────────────────────────────────────────────────────────────────────────

def find_or_create_customer(order):
    """
    Sucht den Kunden der Bestellung per E-Mail in JDS Management; legt ihn an,
    falls er dort noch nicht existiert. Gibt die JDS-Kunden-ID zurueck oder
    None bei Fehler.
    """
    url = f"{settings.JDS_API_BASE_URL}/api/v2/customers/"
    payload = {
        "email": order.email,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "phone": order.phone,
        "address": order.address,
        "zip_code": order.zip_code,
        "city": order.city,
        "company_name": order.company_name or "",
        "vat_number": order.vat_number or "",
        # Erlaubt JDS Management, per E-Mail zu deduplizieren statt Dubletten anzulegen.
        "external_source": "joel-digitals-homepage",
    }
    try:
        resp = requests.post(url, headers=get_api_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        customer_id = data.get("id") or data.get("customer_id") or data.get("customer_number")
        if not customer_id:
            logger.error(f"JDS API find_or_create_customer: keine ID in Antwort für Order {order.id}: {data}")
            return None
        return str(customer_id)
    except requests.RequestException as e:
        logger.error(f"JDS API find_or_create_customer failed for Order {order.id}: {e}")
        return None


def push_order(order):
    """
    Legt den Kunden (falls noetig) in JDS Management an und uebertraegt danach
    die Bestellung, damit sie dort im Auftragsbuch sichtbar ist. Aktualisiert
    Order.jds_customer_id / jds_synced_at / jds_sync_error zur Nachverfolgung
    im Admin. Wird best-effort aufgerufen (z.B. wenn eine Order 'Paid' wird)
    und darf den Checkout niemals blockieren.
    """
    customer_id = order.jds_customer_id or find_or_create_customer(order)
    if not customer_id:
        order.jds_sync_error = "Kunde konnte nicht in JDS Management angelegt/gefunden werden."
        order.save(update_fields=["jds_sync_error"])
        return False

    url = f"{settings.JDS_API_BASE_URL}/api/v2/orders/"
    payload = {
        "external_order_id": str(order.id),
        "customer_id": customer_id,
        "status": order.status,
        "total_amount": str(order.total_amount),
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "product_number": item.app.product_number if item.app else None,
                "name": item.get_name(),
                "quantity": item.quantity,
                "price": str(item.price),
            }
            for item in order.items.select_related("app", "package").all()
        ],
    }
    try:
        resp = requests.post(url, headers=get_api_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        order.jds_customer_id = customer_id
        order.jds_synced_at = timezone.now()
        order.jds_sync_error = ""
        order.save(update_fields=["jds_customer_id", "jds_synced_at", "jds_sync_error"])
        logger.info(f"JDS API: Order {order.id} synced (customer {customer_id})")
        return True
    except requests.RequestException as e:
        order.jds_customer_id = customer_id
        order.jds_sync_error = str(e)
        order.save(update_fields=["jds_customer_id", "jds_sync_error"])
        logger.error(f"JDS API push_order failed for Order {order.id}: {e}")
        return False
