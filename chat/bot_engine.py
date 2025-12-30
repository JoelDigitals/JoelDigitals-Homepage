# chat/bot_engine.py
import json
import os
import re
import random
import difflib
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.json")
LEARNED_FILE = os.path.join(BASE_DIR, "learned.json")

# Lade Wissensbasen
def load_json(filepath, default=None):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default or {}
    return default or {}

KNOWLEDGE = load_json(KNOWLEDGE_FILE, {"de": {}, "en": {}})
LEARNED = load_json(LEARNED_FILE, {"de": {}, "en": {}})

# Chat-Kontext speichern (letzte 10 Nachrichten)
CHAT_HISTORY = defaultdict(list)

# ========================================
# 🔧 HILFSFUNKTIONEN
# ========================================

def normalize_text(text):
    """Entfernt Sonderzeichen und Leerzeichen"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def detect_language(text):
    """Automatische Spracherkennung (DE/EN)"""
    de_words = ["was", "wie", "preis", "kosten", "kann", "hallo", "danke", "öffnungszeiten"]
    en_words = ["what", "how", "price", "cost", "can", "hello", "thanks", "hours"]
    
    text_lower = text.lower()
    de_score = sum(1 for word in de_words if word in text_lower)
    en_score = sum(1 for word in en_words if word in text_lower)
    
    return "de" if de_score >= en_score else "en"

def fuzzy_match(text, keywords, threshold=0.7):
    """Fuzzy-Matching für fehlertolerante Suche"""
    text_words = normalize_text(text).split()
    for word in text_words:
        matches = difflib.get_close_matches(word, keywords, n=1, cutoff=threshold)
        if matches:
            return True
    return False

def add_to_history(session_id, question, answer, max_len=10):
    """Speichert Chat-Verlauf für Kontextbezug"""
    CHAT_HISTORY[session_id].append({"q": question, "a": answer})
    if len(CHAT_HISTORY[session_id]) > max_len:
        CHAT_HISTORY[session_id].pop(0)

def get_last_topic(session_id):
    """Erkennt letztes Thema aus Chat-Historie"""
    if session_id in CHAT_HISTORY and CHAT_HISTORY[session_id]:
        return CHAT_HISTORY[session_id][-1].get("topic")
    return None

# ========================================
# 🎯 INTENT-ERKENNUNG
# ========================================

def detect_intent(text, lang):
    """Erkennt die Absicht des Nutzers"""
    text = normalize_text(text)
    
    intents = {
        "greeting": {
            "de": ["hallo", "hi", "hey", "guten", "servus", "moin"],
            "en": ["hello", "hi", "hey", "good morning", "good evening"]
        },
        "farewell": {
            "de": ["tschüss", "ciao", "bye", "wiedersehen"],
            "en": ["bye", "goodbye", "see you", "farewell"]
        },
        "thanks": {
            "de": ["danke", "vielen dank", "thx", "merci"],
            "en": ["thanks", "thank you", "thx", "cheers"]
        },
        "price": {
            "de": ["preis", "kosten", "kostet", "viel", "gebühr", "bezahlen"],
            "en": ["price", "cost", "costs", "fee", "pay", "payment"]
        },
        "features": {
            "de": ["funktion", "feature", "was kann", "eigenschaften", "möglichkeiten"],
            "en": ["feature", "function", "what can", "capability", "abilities"]
        },
        "contact": {
            "de": ["kontakt", "erreichen", "telefon", "email", "anrufen", "schreiben"],
            "en": ["contact", "reach", "phone", "email", "call", "write"]
        },
        "hours": {
            "de": ["öffnungszeiten", "geöffnet", "wann", "geschlossen"],
            "en": ["opening hours", "open", "when", "closed", "hours"]
        },
        "help": {
            "de": ["hilfe", "helfen", "unterstützung", "problem"],
            "en": ["help", "support", "assistance", "problem"]
        }
    }
    
    for intent, keywords in intents.items():
        if fuzzy_match(text, keywords.get(lang, []), threshold=0.65):
            return intent
    
    return "general"

# ========================================
# 🔍 PRODUKT-ERKENNUNG
# ========================================

def detect_products(text, kb):
    """Erkennt erwähnte Produkte/Services"""
    text_norm = normalize_text(text)
    detected = []
    
    product_keys = ["jds_management", "auftragnetz", "jds_appstore", "logo_design", 
                    "support", "hosting", "webentwicklung", "digitalisierung"]
    
    for key in product_keys:
        prod = kb.get(key, {})
        names = [key.lower()]
        
        if "name" in prod:
            names.append(normalize_text(prod["name"]))
        if "keywords" in prod:
            names.extend([normalize_text(kw) for kw in prod["keywords"]])
        
        if any(name in text_norm for name in names):
            detected.append(key)
    
    return detected

# ========================================
# 💬 ANTWORT-GENERIERUNG
# ========================================

def generate_response(question, lang=None, session_id="default"):
    """Hauptfunktion zur Antwortgenerierung"""
    
    # Spracherkennung
    lang = lang or detect_language(question)
    kb = KNOWLEDGE.get(lang, KNOWLEDGE.get("de", {}))
    learned = LEARNED.get(lang, {})
    
    # Intent erkennen
    intent = detect_intent(question, lang)
    q_lower = question.lower()
    
    # ========================================
    # 1️⃣ BEGRÜSSUNG
    # ========================================
    if intent == "greeting":
        responses = kb.get("begrüßung", kb.get("greeting", ["Hallo! Wie kann ich helfen?"]))
        return random.choice(responses)
    
    # ========================================
    # 2️⃣ VERABSCHIEDUNG
    # ========================================
    if intent == "farewell":
        responses = kb.get("verabschiedung", kb.get("farewell", ["Auf Wiedersehen!"]))
        return random.choice(responses)
    
    # ========================================
    # 3️⃣ DANKE
    # ========================================
    if intent == "thanks":
        responses = kb.get("danke", kb.get("thanks", ["Gerne!"]))
        return random.choice(responses)
    
    # ========================================
    # 4️⃣ ÖFFNUNGSZEITEN
    # ========================================
    if intent == "hours":
        meta = kb.get("meta", {})
        hours = meta.get("öffnungszeiten", meta.get("opening_hours", {}))
        
        today = datetime.now().strftime("%A").lower()
        today_hours = hours.get(today, "geschlossen" if lang == "de" else "closed")
        
        response = "🕐 **Öffnungszeiten**\n" if lang == "de" else "🕐 **Opening Hours**\n"
        response += f"**Heute ({today.title()}):** {today_hours}\n\n"
        
        for day, time in hours.items():
            if day not in ["aktuelle_öffnungszeiten", "actual_opening_hours"]:
                response += f"**{day.title()}:** {time}\n"
        
        return response.strip()
    
    # ========================================
    # 5️⃣ KONTAKT
    # ========================================
    if intent == "contact":
        meta = kb.get("meta", {})
        email = meta.get("email", "info@joel-digitals.de")
        phone = meta.get("telefon", meta.get("phone", "+49 1525 3480270"))
        contact_url = meta.get("contact", "https://joel-digitals.de/contact")
        
        return (
            f"📞 **Kontakt**\n"
            f"📧 E-Mail: {email}\n"
            f"☎️ Telefon: {phone}\n"
            f"🌐 Kontaktformular: {contact_url}"
        )
    
    # ========================================
    # 6️⃣ HILFE/SUPPORT
    # ========================================
    if intent == "help":
        support = kb.get("support", {})
        name = support.get("name", "Joel Digitals Support")
        desc = support.get("beschreibung", support.get("description", ""))
        url = support.get("website", "https://joel-digitals.de/contact")
        
        return f"🆘 **{name}**\n{desc}\n\n🔗 Zum Support: {url}"
    
    # ========================================
    # 7️⃣ PRODUKT-ANFRAGEN
    # ========================================
    detected_products = detect_products(question, kb)
    
    if detected_products:
        answers = []
        
        for prod_key in detected_products:
            prod = kb.get(prod_key, {})
            name = prod.get("name", prod_key.title())
            desc = prod.get("beschreibung", prod.get("description", ""))
            short = prod.get("kurz", prod.get("short", ""))
            
            # PREIS-ANFRAGE
            if intent == "price":
                price = prod.get("preis", prod.get("price"))
                if price:
                    answers.append(f"💰 **Preis für {name}:** {price}")
                else:
                    answers.append(f"Für den Preis von {name} kontaktiere uns bitte direkt.")
            
            # FEATURES-ANFRAGE
            elif intent == "features":
                features = prod.get("features", prod.get("services", []))
                if isinstance(features, dict):
                    feat_list = "\n".join([f"• **{k.title()}:** {v}" for k, v in features.items()])
                elif isinstance(features, list):
                    feat_list = "\n".join([f"• {f}" for f in features])
                else:
                    feat_list = "Keine Details verfügbar."
                
                answers.append(f"⚙️ **Funktionen von {name}:**\n{feat_list}")
            
            # ALLGEMEINE INFO
            else:
                info = f"📘 **{name}**\n{desc or short}"
                
                # Links hinzufügen
                if "docs" in prod or "website" in prod:
                    url = prod.get("docs", prod.get("website"))
                    info += f"\n\n🔗 Mehr Infos: {url}"
                
                if "register" in prod:
                    info += f"\n📝 Registrierung: {prod['register']}"
                
                answers.append(info)
        
        if answers:
            response = "\n\n".join(answers)
            add_to_history(session_id, question, response)
            return response
    
    # ========================================
    # 8️⃣ GELERNTE ANTWORTEN
    # ========================================
    q_norm = normalize_text(question)
    for learned_q, learned_data in learned.items():
        if normalize_text(learned_q) in q_norm or q_norm in normalize_text(learned_q):
            answer = learned_data.get("beschreibung", learned_data.get("answer", ""))
            add_to_history(session_id, question, answer)
            return answer
    
    # ========================================
    # 9️⃣ FALLBACK
    # ========================================
    fallback = kb.get("hilfe", kb.get("help", [
        "Ich habe deine Frage leider nicht verstanden. Kannst du sie anders formulieren?",
        "Darüber habe ich leider keine Informationen. Kontaktiere uns gerne direkt!"
    ]))
    
    response = random.choice(fallback) if isinstance(fallback, list) else fallback
    add_to_history(session_id, question, response)
    return response

# ========================================
# 🎯 HAUPTFUNKTION (API-Entry)
# ========================================

def chatbot_answer(question, lang="de", session_id="default"):
    """Öffentliche API-Funktion"""
    return generate_response(question, lang, session_id)
