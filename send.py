from datetime import datetime, timedelta, timezone
from sib_api_v3_sdk import ApiClient, Configuration, EmailCampaignsApi, CreateEmailCampaign
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

# ------------------
# API-Key konfigurieren
# ------------------
configuration = Configuration()
configuration.api_key['api-key'] = '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'

api_client = ApiClient(configuration)
api_instance = EmailCampaignsApi(api_client)

# ------------------
# Zeitpunkt: 10 Minuten in der Zukunft
# ------------------
scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=10)
scheduled_iso = scheduled_time.isoformat(timespec='seconds')

# ------------------
# Kampagne definieren (über Liste)
# ------------------
email_campaign = CreateEmailCampaign(
    name="Test-Mail an einzelne Adresse",
    subject="Test-Betreff",
    sender={"name": "Joel Digitals", "email": "no-reply@joel-digitals.de"},
    recipients={"listIds": [2]},  # <-- deine Testliste-ID einsetzen
    html_content="<html><body><h1>Hallo!</h1><p>Dies ist ein Test-Mail an eine einzelne Adresse.</p></body></html>",
    scheduled_at=scheduled_iso
)

# ------------------
# Kampagne erstellen
# ------------------
try:
    api_response = api_instance.create_email_campaign(email_campaign)
    pprint(api_response)
except ApiException as e:
    print("Fehler beim Erstellen der Kampagne: %s\n" % e)
