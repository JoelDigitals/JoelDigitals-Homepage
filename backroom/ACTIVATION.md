# Backroom: Aktivierung / Lizenzcodes (z.B. Softwarelizenzen)

Manche Backroom-Produkte (z.B. Softwarelizenzen) sind nicht "einfach ein Download",
sondern brauchen nach dem Kauf einen Aktivierungscode. Damit das nicht vergessen
wird, hat `BackroomProduct` ein Flag:

```python
product.requires_activation  # BooleanField, Default False
```

Beim Anlegen/Bearbeiten eines Backroom-Produkts (Django-Admin) einfach ankreuzen,
wenn das Produkt nach dem Kauf eine manuelle Aktivierung braucht.

## Bezahlung läuft normal über Cart/Checkout

Backroom-Produkte gehen genau wie Apps/Packages durch den normalen Warenkorb
und Checkout (`CartItem.backroom_product`, `OrderItem.backroom_product`, siehe
`shop_ourapps/models.py`). Es gibt keinen separaten Zahlungsweg — das Flag
`requires_activation` steuert nur, ob nach der Zahlung noch ein Code verschickt
werden muss.

## Wie der Code zum Kunden kommt: bestehender Ablauf wiederverwenden

Es gibt dafür **bereits** einen fertigen, manuellen Ablauf für Bestellungen
(aktuell für App-Lizenzen genutzt) — für Backroom-Aktivierungscodes wird exakt
derselbe Weg verwendet, es muss nichts Neues gebaut werden:

1. Admin öffnet die Bestellung in `order_admin`
   (`shop_ourapps/views.py::order_admin`, URL `/admin-sales/orders/`).
2. Im Formular "E-Mail senden" (`SendAccessMailForm`) gibt es das Feld
   `registration_codes`, Format: `Produktname1:Code1, Produktname2:Code2`.
   Für ein Backroom-Produkt einfach `product.name` als Schlüssel benutzen,
   z.B. `JDS Security Lizenz:ABCD-1234-EFGH`.
3. Das Formular ruft `OrderAutomationService.mark_as_sent(order, codes_str)`
   auf (`shop_ourapps/services/automation_service.py`). Das setzt
   `Order.registration_code`, `registration_code_sent_at` und den Status auf
   `'In Delivery'`.
4. Der bestehende Cron/Automation-Flow übernimmt den Rest automatisch:
   nach 30 Minuten → `'Delivered'`, nach 12–72h zufällig eine Review-Mail →
   `'Finished'` (siehe `OrderAutomationService.auto_deliver_after_30_minutes`
   und `.send_review_emails`).

Es gibt aktuell **keinen** separaten Code pro `OrderItem` in der DB — der Code
ist ein freier Text auf der ganzen Bestellung (`Order.registration_code`),
mehrere Produkte in einer Bestellung werden einfach als
`"Produkt A:CodeA, Produkt B:CodeB"` in dasselbe Feld geschrieben. Für Backroom
reicht das genauso wie für Apps.

## Woran der Admin erkennt, dass ein Code fehlt

In `order_admin` über die Bestellpositionen iterieren und prüfen:

```python
for item in order.items.all():
    if item.backroom_product and item.backroom_product.requires_activation:
        # Hinweis anzeigen: "Aktivierungscode für {item.backroom_product.name} nötig"
```

Das ist aktuell **nicht** visuell im Template markiert — nur das Datenmodell-Flag
existiert. Wer das komfortabler machen will: in
`shop_ourapps/templates/apps/order_admin.html` (bzw. der entsprechenden
Bestell-Detailansicht) eine Bedingung wie oben ergänzen und einen Warnhinweis
neben der Bestellposition rendern.

## Falls später ein vollautomatischer Ablauf gebraucht wird

Der jetzige Weg ist bewusst manuell (Admin tippt/kopiert den Code rein). Für
eine spätere Automatisierung (z.B. Code wird bei Zahlungseingang automatisch
aus einem Pool gezogen und direkt gemailt) wäre der Einstiegspunkt
`OrderAutomationService.set_paid()` in `shop_ourapps/services/automation_service.py`
— dort werden beim Bezahlt-Setzen schon `Purchase`-Einträge erstellt; dort
könnte man analog für `item.backroom_product.requires_activation`-Items aus
einem Codepool ziehen und direkt `mark_as_sent()` aufrufen statt auf den Admin
zu warten. Das ist aktuell nicht gebaut, nur als Ansatzpunkt dokumentiert.
