import requests
from django.conf import settings

def get_paypal_access_token():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token" if settings.PAYPAL_ENVIRONMENT == "sandbox" else "https://api-m.paypal.com/v1/oauth2/token"
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data, auth=auth)
    response.raise_for_status()
    return response.json()["access_token"]

def create_paypal_order(amount, invoice_id, return_url, cancel_url):
    access_token = get_paypal_access_token()
    url = "https://api-m.sandbox.paypal.com/v2/checkout/orders" if settings.PAYPAL_ENVIRONMENT == "sandbox" else "https://api-m.paypal.com/v2/checkout/orders"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    # Formatieren des Betrags auf zwei Dezimalstellen
    formatted_amount = "{:.2f}".format(amount)
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "EUR",
                    "value": formatted_amount
                },
                "invoice_id": str(invoice_id)
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def capture_paypal_order(order_id):
    access_token = get_paypal_access_token()
    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture" if settings.PAYPAL_ENVIRONMENT == "sandbox" else f"https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()
