from django.core.management.base import BaseCommand
from main.models import FAQ


def _expand_answer_de(question, answer):
    """Erzeugt detail_content_de basierend auf Frage und Antwort."""
    q = question.lower()
    base = f"<p>Im Folgenden finden Sie ausführliche Hintergrundinformationen und praktische Hinweise zu dieser Frage.</p>"

    if any(w in q for w in ["passwort", "anmelden", "login", "registrieren", "konto", "benutzername"]):
        base += f"""
<h3>Schritt-für-Schritt-Anleitung</h3>
{answer}
<h3>Wichtige Hinweise</h3>
<ul>
<li>Verwenden Sie ein sicheres Passwort mit mindestens 12 Zeichen.</li>
<li>Geben Sie Ihre Zugangsdaten niemals an Dritte weiter.</li>
<li>Bei Problemen mit der Anmeldung kontaktieren Sie unseren Support.</li>
</ul>
<h3>Was tun bei Problemen?</h3>
<p>Sollten Sie Schwierigkeiten haben, überprüfen Sie bitte: Haben Sie Ihre E-Mail-Adresse richtig eingegeben? Ist Ihr Passwort korrekt? Haben Sie Ihr Konto bereits bestätigt? Unser Support hilft Ihnen gerne weiter.</p>"""

    elif any(w in q for w in ["zahlung", "kreditkarte", "paypal", "überweisung", "rechnung", "vorkasse"]):
        base += f"""
<h3>Übersicht der Zahlungsmethoden</h3>
{answer}
<h3>Sicherheit Ihrer Zahlungsdaten</h3>
<p>Alle Zahlungen werden über PCI-DSS-zertifizierte Zahlungsdienstleister abgewickelt. Ihre vollständigen Zahlungsdaten werden nicht auf unseren Servern gespeichert. Die Übertragung erfolgt ausschließlich über verschlüsselte Verbindungen (SSL/TLS).</p>
<h3>Was passiert nach der Zahlung?</h3>
<p>Nach erfolgreicher Zahlung erhalten Sie umgehend eine Bestätigung per E-Mail. Bei Vorauszahlung per Banküberweisung wird die Bestellung nach Geldeingang bearbeitet. Bei Problemen mit der Zahlung kontaktieren Sie bitte unseren Support.</p>"""

    elif any(w in q for w in ["rabatt", "coupon", "aktion", "gutschein", "sale", "angebot"]):
        base += f"""
<h3>So nutzen Sie Rabattaktionen</h3>
{answer}
<h3>Bedingungen und Hinweise</h3>
<ul>
<li>Rabattcodes sind nur innerhalb des angegebenen Zeitraums gültig.</li>
<li>Pro Bestellung kann nur ein Rabattcode verwendet werden.</li>
<li>Rabattaktionen können nicht mit anderen Aktionen kombiniert werden.</li>
<li>Bei Fragen zu Ihrem Rabattcode kontaktieren Sie unseren Support.</li>
</ul>"""

    elif any(w in q for w in ["download", "herunterladen", "app", "software", "produkt"]):
        base += f"""
<h3>Details zum Download</h3>
{answer}
<h3>Systemvoraussetzungen</h3>
<p>Bitte stellen Sie sicher, dass Ihr System die Mindestanforderungen erfüllt. Die genauen Systemvoraussetzungen finden Sie auf der Produktseite der jeweiligen App. In der Regel werden die aktuellen Versionen von Windows, macOS und Linux unterstützt.</p>
<h3>Probleme beim Download?</h3>
<p>Sollte der Download nicht funktionieren, überprüfen Sie bitte Ihre Internetverbindung und versuchen Sie es erneut. Falls das Problem bestehen bleibt, kontaktieren Sie unseren Support.</p>"""

    elif any(w in q for w in ["lizenz", "aktivieren", "produktschlüssel", "übertragen"]):
        base += f"""
<h3>Lizenzinformationen im Detail</h3>
{answer}
<h3>Wichtige Hinweise zur Lizenz</h3>
<ul>
<li>Bewahren Sie Ihren Lizenzschlüssel sicher auf.</li>
<li>Eine Lizenz gilt in der Regel für ein Gerät – Ausnahmen sind auf der Produktseite vermerkt.</li>
<li>Bei Verlust Ihres Lizenzschlüssels kontaktieren Sie unseren Support.</li>
<li>Lizenzübertragungen sind nur begrenzt möglich.</li>
</ul>"""

    elif any(w in q for w in ["webinar", "aufzeichnung", "teilnahme"]):
        base += f"""
<h3>Webinar-Teilnahme im Detail</h3>
{answer}
<h3>Technische Voraussetzungen</h3>
<p>Sie benötigen: einen stabilen Internetzugang (DSL oder besser), einen aktuellen Webbrowser, Lautsprecher oder Kopfhörer. Für interaktive Webinare empfehlen wir ein Mikrofon.</p>
<h3>Ablauf eines Webinars</h3>
<p>Nach der Anmeldung erhalten Sie eine Bestätigung und vor Beginn den Zugangslink. Das Webinar dauert in der Regel 30–60 Minuten inklusive Fragerunde. Bei verpassten Webinaren erhalten Sie ggf. eine Aufzeichnung.</p>"""

    elif any(w in q for w in ["support", "ticket", "bug", "fehler", "kontakt"]):
        base += f"""
<h3>Support-Optionen im Überblick</h3>
{answer}
<h3>So erreichen Sie uns</h3>
<ul>
<li>E-Mail: support@joeldigitals.com</li>
<li>Kontaktformular: über unsere Website</li>
<li>Ticket-System: in Ihrem Konto</li>
<li>Telefon: während der Geschäftszeiten</li>
</ul>
<h3>Support-Zeiten</h3>
<p>Unser Support ist von Montag bis Freitag, 9:00 bis 18:00 Uhr für Sie da. Außerhalb dieser Zeiten eingehende Anfragen werden am nächsten Werktag bearbeitet.</p>"""

    elif any(w in q for w in ["daten", "sicherheit", "datenschutz", "cookie", "dsgvo"]):
        base += f"""
<h3>Datenschutz und Sicherheit im Detail</h3>
{answer}
<h3>Unsere Sicherheitsmaßnahmen</h3>
<ul>
<li>SSL/TLS-Verschlüsselung für die gesamte Datenübertragung</li>
<li>Regelmäßige Sicherheitsupdates und Backups</li>
<li>DSGVO-konforme Datenverarbeitung</li>
<li>Sichere Serverstandorte in Deutschland</li>
</ul>
<h3>Ihre Rechte</h3>
<p>Gemäß DSGVO haben Sie das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Verarbeitung Ihrer Daten. Kontaktieren Sie uns jederzeit unter datenschutz@joeldigitals.com.</p>"""

    elif any(w in q for w in ["vorbestellung", "pre-order", "preorder", "release"]):
        base += f"""
<h3>Vorbestellungen im Detail</h3>
{answer}
<h3>Wichtige Informationen zur Vorbestellung</h3>
<ul>
<li>Der Preis bei Vorbestellung ist in der Regel günstiger als nach dem Release.</li>
<li>Die Zahlung erfolgt zum Zeitpunkt der Bestellung.</li>
<li>Sie erhalten das Produkt automatisch zum Release-Datum.</li>
<li>Sie werden per E-Mail benachrichtigt, sobald das Produkt verfügbar ist.</li>
</ul>"""

    elif any(w in q for w in ["watchlist", "merkzettel", "benachrichtigen"]):
        base += f"""
<h3>Watchlist-Funktion im Detail</h3>
{answer}
<h3>Tipps zur Nutzung</h3>
<ul>
<li>Sie können beliebig viele Produkte zur Watchlist hinzufügen.</li>
<li>Sie erhalten eine E-Mail, sobald ein Produkt wieder verfügbar ist.</li>
<li>Entfernen Sie Produkte von der Watchlist, sobald Sie sie nicht mehr benötigen.</li>
<li>Die Watchlist ist nur für eingeloggte Benutzer verfügbar.</li>
</ul>"""

    elif any(w in q for w in ["affiliate", "provision", "empfehlen", "partner"]):
        base += f"""
<h3>Affiliate-Programm im Detail</h3>
{answer}
<h3>Vorteile des Programms</h3>
<ul>
<li>Sie erhalten einen persönlichen Empfehlungslink.</li>
<li>Provisionen werden monatlich ab 50 € ausgezahlt.</li>
<li>Sie können beliebig viele Produkte bewerben.</li>
<li>Keine Mindestanzahl an Empfehlungen erforderlich.</li>
</ul>"""

    elif any(w in q for w in ["stornieren", "widerruf", "zurückgeben", "rückerstattung", "rückgabe"]):
        base += f"""
<h3>Widerruf und Rückgabe im Detail</h3>
{answer}
<h3>Rückgabeprozess</h3>
<ol>
<li>Kontaktieren Sie uns per E-Mail oder Kontaktformular.</li>
<li>Sie erhalten eine Rückgabeanleitung und ggf. ein Rücksendeetikett.</li>
<li>Senden Sie die Ware innerhalb von 14 Tagen zurück.</li>
<li>Die Rückerstattung erfolgt innerhalb von 5–10 Werktagen nach Eingang.</li>
</ol>
<h3>Ausnahmen</h3>
<p>Bei digitalen Produkten, die bereits heruntergeladen oder aktiviert wurden, ist ein Widerruf ausgeschlossen. Bei physischen Produkten tragen Sie die Rücksendekosten.</p>"""

    elif any(w in q for w in ["bestellung", "lieferung", "versand", "tracking", "verfolgen"]):
        base += f"""
<h3>Bestell- und Lieferprozess im Detail</h3>
{answer}
<h3>Status Ihrer Bestellung</h3>
<p>Sie können den Status Ihrer Bestellung jederzeit in Ihrem Konto unter 'Meine Bestellungen' einsehen. Bei Versand erhalten Sie eine E-Mail mit einem Tracking-Link.</p>
<h3>Lieferzeiten</h3>
<p>Digitale Produkte: ca. 2 Werktage. Physische Produkte: 2–5 Werktage innerhalb Deutschlands. Internationale Lieferungen können länger dauern.</p>"""

    elif any(w in q for w in ["service", "entwicklung", "hosting", "consulting", "beratung", "wartung"]):
        base += f"""
<h3>Unsere Dienstleistungen im Detail</h3>
{answer}
<h3>So arbeiten wir</h3>
<ol>
<li><strong>Beratung</strong> – Wir analysieren Ihre Anforderungen und entwickeln eine maßgeschneiderte Lösung.</li>
<li><strong>Planung</strong> – Wir erstellen ein detailliertes Konzept und einen Zeitplan.</li>
<li><strong>Umsetzung</strong> – Wir entwickeln Ihre Lösung mit modernsten Technologien.</li>
<li><strong>Support</strong> – Wir stehen Ihnen auch nach der Fertigstellung zur Seite.</li>
</ol>
<p>Kontaktieren Sie uns für ein unverbindliches Angebot.</p>"""

    elif any(w in q for w in ["bewerbung", "job", "praktikum", "karriere", "stelle"]):
        base += f"""
<h3>Bewerbungsprozess im Detail</h3>
{answer}
<h3>Unser Bewerbungsprozess</h3>
<ol>
<li><strong>Bewerbung einreichen</strong> – Senden Sie Ihre Unterlagen per E-Mail.</li>
<li><strong>Prüfung</strong> – Wir sichten Ihre Bewerbung innerhalb von 14 Tagen.</li>
<li><strong>Interview</strong> – Bei Interesse laden wir Sie zu einem Gespräch ein.</li>
<li><strong>Entscheidung</strong> – Sie erhalten zeitnah eine Rückmeldung.</li>
</ol>
<p>Wir freuen uns auf Ihre Bewerbung!</p>"""

    elif any(w in q for w in ["gründerwoche", "gründer", "jubiläum"]):
        base += f"""
<h3>Gründerwochen – Details</h3>
{answer}
<h3>Wie bleibe ich informiert?</h3>
<p>Um keine Aktion zu verpassen, abonnieren Sie unseren Newsletter und folgen Sie uns auf Social Media. Der genaue Zeitraum und die Angebote werden frühzeitig angekündigt.</p>"""

    else:
        base += f"""
<h3>Ausführliche Informationen</h3>
{answer}
<h3>Weiterführende Hinweise</h3>
<p>Bei weiteren Fragen zu diesem Thema können Sie jederzeit unseren Support kontaktieren oder in verwandten FAQ-Artikeln nachlesen. Wir sind bemüht, Ihnen alle notwendigen Informationen bereitzustellen.</p>"""

    return base


def _expand_answer_en(question, answer):
    """Erzeugt detail_content_en basierend auf Frage und Antwort."""
    q = question.lower()
    base = f"<p>Below you will find detailed background information and practical tips related to this question.</p>"

    if any(w in q for w in ["password", "login", "register", "account", "username", "sign in"]):
        base += f"""
<h3>Step-by-Step Guide</h3>
{answer}
<h3>Important Notes</h3>
<ul>
<li>Use a strong password with at least 12 characters.</li>
<li>Never share your login credentials with third parties.</li>
<li>If you have problems logging in, contact our support.</li>
</ul>
<h3>What to do if you have issues?</h3>
<p>If you are having difficulties, please check: Did you enter your email address correctly? Is your password correct? Have you confirmed your account? Our support team is happy to help.</p>"""

    elif any(w in q for w in ["payment", "credit card", "paypal", "transfer", "invoice", "prepayment"]):
        base += f"""
<h3>Payment Methods Overview</h3>
{answer}
<h3>Security of Your Payment Data</h3>
<p>All payments are processed through PCI-DSS certified payment providers. Your complete payment data is not stored on our servers. All transmission occurs via encrypted connections (SSL/TLS).</p>
<h3>What happens after payment?</h3>
<p>After successful payment, you will immediately receive a confirmation by email. For prepayment by bank transfer, the order will be processed upon receipt of payment. If you encounter payment issues, please contact our support.</p>"""

    elif any(w in q for w in ["discount", "coupon", "promotion", "voucher", "sale", "offer"]):
        base += f"""
<h3>How to Use Discounts</h3>
{answer}
<h3>Terms and Conditions</h3>
<ul>
<li>Discount codes are only valid within the specified period.</li>
<li>Only one discount code can be used per order.</li>
<li>Discounts cannot be combined with other promotions.</li>
<li>If you have questions about your discount code, contact our support.</li>
</ul>"""

    elif any(w in q for w in ["download", "app", "software", "product"]):
        base += f"""
<h3>Download Details</h3>
{answer}
<h3>System Requirements</h3>
<p>Please ensure your system meets the minimum requirements. The exact system requirements can be found on the product page of each app. Generally, the latest versions of Windows, macOS, and Linux are supported.</p>
<h3>Download Issues?</h3>
<p>If the download does not work, please check your internet connection and try again. If the problem persists, contact our support.</p>"""

    elif any(w in q for w in ["license", "activate", "product key", "transfer"]):
        base += f"""
<h3>License Information in Detail</h3>
{answer}
<h3>Important License Notes</h3>
<ul>
<li>Keep your license key in a safe place.</li>
<li>A license typically applies to one device – exceptions are noted on the product page.</li>
<li>If you lose your license key, contact our support.</li>
<li>License transfers are only possible to a limited extent.</li>
</ul>"""

    elif any(w in q for w in ["webinar", "recording", "participate"]):
        base += f"""
<h3>Webinar Participation in Detail</h3>
{answer}
<h3>Technical Requirements</h3>
<p>You need: a stable internet connection (DSL or better), an up-to-date web browser, speakers or headphones. For interactive webinars, we recommend a microphone.</p>
<h3>Webinar流程</h3>
<p>After registration you will receive a confirmation and the access link before the start. The webinar usually lasts 30–60 minutes including Q&A. If you miss a webinar, you may receive a recording.</p>"""

    elif any(w in q for w in ["support", "ticket", "bug", "error", "contact"]):
        base += f"""
<h3>Support Options Overview</h3>
{answer}
<h3>How to Reach Us</h3>
<ul>
<li>Email: support@joeldigitals.com</li>
<li>Contact form: via our website</li>
<li>Ticket system: in your account</li>
<li>Phone: during business hours</li>
</ul>
<h3>Support Hours</h3>
<p>Our support is available Monday to Friday, 9:00 AM to 6:00 PM. Inquiries received outside these hours will be processed on the next business day.</p>"""

    elif any(w in q for w in ["data", "security", "privacy", "cookie", "gdpr"]):
        base += f"""
<h3>Data Protection and Security in Detail</h3>
{answer}
<h3>Our Security Measures</h3>
<ul>
<li>SSL/TLS encryption for all data transmission</li>
<li>Regular security updates and backups</li>
<li>GDPR-compliant data processing</li>
<li>Secure server locations in Germany</li>
</ul>
<h3>Your Rights</h3>
<p>Under GDPR, you have the right to access, correct, delete, and restrict the processing of your data. Contact us at any time at datenschutz@joeldigitals.com.</p>"""

    elif any(w in q for w in ["pre-order", "preorder", "release"]):
        base += f"""
<h3>Pre-Orders in Detail</h3>
{answer}
<h3>Important Pre-Order Information</h3>
<ul>
<li>The pre-order price is usually lower than after release.</li>
<li>Payment is processed at the time of ordering.</li>
<li>You will receive the product automatically on the release date.</li>
<li>You will be notified by email when the product is available.</li>
</ul>"""

    elif any(w in q for w in ["watchlist", "notif"]):
        base += f"""
<h3>Watchlist Function in Detail</h3>
{answer}
<h3>Usage Tips</h3>
<ul>
<li>You can add any number of products to your watchlist.</li>
<li>You will receive an email when a product is back in stock.</li>
<li>Remove products from the watchlist when you no longer need them.</li>
<li>The watchlist is only available for logged-in users.</li>
</ul>"""

    elif any(w in q for w in ["affiliate", "commission", "refer", "partner"]):
        base += f"""
<h3>Affiliate Program in Detail</h3>
{answer}
<h3>Program Benefits</h3>
<ul>
<li>You receive a personal referral link.</li>
<li>Commissions are paid out monthly from €50.</li>
<li>You can promote any number of products.</li>
<li>No minimum number of referrals required.</li>
</ul>"""

    elif any(w in q for w in ["cancel", "withdrawal", "return", "refund"]):
        base += f"""
<h3>Cancellation and Returns in Detail</h3>
{answer}
<h3>Return Process</h3>
<ol>
<li>Contact us by email or contact form.</li>
<li>You will receive return instructions and possibly a return label.</li>
<li>Send the goods back within 14 days.</li>
<li>The refund will be made within 5–10 business days upon receipt.</li>
</ol>
<h3>Exceptions</h3>
<p>For digital products that have already been downloaded or activated, cancellation is excluded. For physical products, you bear the return shipping costs.</p>"""

    elif any(w in q for w in ["order", "delivery", "shipping", "track"]):
        base += f"""
<h3>Order and Delivery Process in Detail</h3>
{answer}
<h3>Order Status</h3>
<p>You can check the status of your order at any time in your account under 'My Orders'. When shipped, you will receive an email with a tracking link.</p>
<h3>Delivery Times</h3>
<p>Digital products: approx. 2 business days. Physical products: 2–5 business days within Germany. International deliveries may take longer.</p>"""

    elif any(w in q for w in ["service", "development", "hosting", "consulting", "maintenance"]):
        base += f"""
<h3>Our Services in Detail</h3>
{answer}
<h3>How We Work</h3>
<ol>
<li><strong>Consultation</strong> – We analyze your requirements and develop a tailored solution.</li>
<li><strong>Planning</strong> – We create a detailed concept and timeline.</li>
<li><strong>Implementation</strong> – We develop your solution using cutting-edge technologies.</li>
<li><strong>Support</strong> – We are here for you even after completion.</li>
</ol>
<p>Contact us for a non-binding quote.</p>"""

    elif any(w in q for w in ["application", "job", "internship", "career", "position"]):
        base += f"""
<h3>Application Process in Detail</h3>
{answer}
<h3>Our Application Process</h3>
<ol>
<li><strong>Submit application</strong> – Send your documents by email.</li>
<li><strong>Review</strong> – We review your application within 14 days.</li>
<li><strong>Interview</strong> – If interested, we invite you for a discussion.</li>
<li><strong>Decision</strong> – You will receive feedback promptly.</li>
</ol>
<p>We look forward to your application!</p>"""

    elif any(w in q for w in ["founder week", "anniversary"]):
        base += f"""
<h3>Founder Weeks – Details</h3>
{answer}
<h3>How to Stay Informed</h3>
<p>To not miss any promotions, subscribe to our newsletter and follow us on social media. The exact period and offers will be announced in good time.</p>"""

    else:
        base += f"""
<h3>Detailed Information</h3>
{answer}
<h3>Further Notes</h3>
<p>If you have further questions on this topic, you can always contact our support or read related FAQ articles. We strive to provide you with all the necessary information.</p>"""

    return base


class Command(BaseCommand):
    help = "Erzeugt detail_content für alle FAQs, die noch keinen haben"

    def handle(self, *args, **options):
        qs = FAQ.objects.filter(detail_content_de="", detail_content_en="")
        updated = 0
        for faq in qs:
            faq.detail_content_de = _expand_answer_de(faq.question_de, faq.answer_de)
            faq.detail_content_en = _expand_answer_en(faq.question_en, faq.answer_en)
            faq.save(update_fields=["detail_content_de", "detail_content_en"])
            updated += 1
            if updated % 20 == 0:
                self.stdout.write(f"{updated} FAQs aktualisiert...")

        self.stdout.write(self.style.SUCCESS(
            f"Fertig! {updated} FAQs mit detail_content befüllt."
        ))
