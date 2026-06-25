import requests
import logging
from django.conf import settings
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
