import json, os, re, random, difflib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.json")

with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
    KNOWLEDGE = json.load(f)

PRODUCTS = ["jds_management", "auftragnetz", "jds_appstore", "logo_design", "support", "Hosting", "webentwicklung", "Digitalisierung"]
CHAT_CONTEXT = []

# ---------------------------
# Hilfsfunktionen
# ---------------------------

def remember_context(question, answer, max_len=5):
    CHAT_CONTEXT.append({"question": question, "answer": answer})
    if len(CHAT_CONTEXT) > max_len:
        CHAT_CONTEXT.pop(0)

def _normalize(text):
    return text.lower().replace(" ", "")

def fuzzy_match_keywords(question, keywords, cutoff=0.6):
    words = re.findall(r'\w+', question.lower())
    for word in words:
        if difflib.get_close_matches(word, keywords, n=1, cutoff=cutoff):
            return True
    return False

def is_price_question(q):
    keywords = ["preis", "kosten", "was kostet", "wie viel", "kostenlos", "gebühr"]
    return fuzzy_match_keywords(q, keywords, cutoff=0.5)

def is_feature_question(q):
    keywords = ["features", "funktion", "funktionen", "eigenschaft", "was kann", "enthalten"]
    return fuzzy_match_keywords(q, keywords, cutoff=0.5)

def detect_product(question, kb):
    """Erkennt das Produkt basierend auf Namen oder typischen Keywords"""
    q_norm = _normalize(question)
    best_score = 0
    best_prod = None
    for key in PRODUCTS:
        prod = kb.get(key, {})
        prod_name = prod.get("name", "").lower().replace(" ", "")
        prod_keywords = [prod_name] + [kw.lower().replace(" ", "") for kw in prod.get("keywords", [])]

        # Direkter Name oder Keyword Match
        if any(kw in q_norm for kw in prod_keywords):
            return key

        # Fuzzy Match
        for kw in prod_keywords:
            score = difflib.SequenceMatcher(None, kw, q_norm).ratio()
            if score > best_score:
                best_score = score
                best_prod = key
    return best_prod if best_score > 0.65 else None

def get_last_product():
    for context in reversed(CHAT_CONTEXT):
        detected = detect_product(context["question"], KNOWLEDGE["de"])
        if detected:
            return detected
    return None

# ---------------------------
# Hauptfunktion
# ---------------------------

import re, random, difflib

def detect_language(text):
    """Erkennt automatisch, ob der Text deutsch oder englisch ist."""
    de_keywords = ["was", "wie", "preis", "kosten", "funktion", "hallo", "danke"]
    en_keywords = ["what", "how", "price", "cost", "feature", "hello", "thanks"]
    text_lower = text.lower()

    de_score = sum(1 for k in de_keywords if k in text_lower)
    en_score = sum(1 for k in en_keywords if k in text_lower)

    if de_score > en_score:
        return "de"
    elif en_score > de_score:
        return "en"
    else:
        return "de"  # Standard: Deutsch

import datetime
import difflib

def correct_spelling(text, vocabulary, cutoff=0.75):
    """Korrigiert einfache Rechtschreibfehler anhand einer Wortliste."""
    words = text.split()
    corrected = []
    for w in words:
        match = difflib.get_close_matches(w.lower(), vocabulary, n=1, cutoff=cutoff)
        corrected.append(match[0] if match else w)
    return " ".join(corrected)

def generate_answer(question, lang=None):
    q = question.strip()
    # -----------------------------
    # Rechtschreibkorrektur
    # -----------------------------
    vocab = ["joel", "digitals", "jds", "management", "auftragnetz", "appstore",
             "logo", "design", "support", "hosting", "webentwicklung", "digitalisierung"]
    q = correct_spelling(q, vocab)

    lang = lang or detect_language(q)
    kb = KNOWLEDGE.get(lang, KNOWLEDGE.get("de", {}))
    answers = []

    q_lower = q.lower()

    # -------------------------
    # 1️⃣ Begrüßung, Danke, Verabschiedung
    # -------------------------
    greetings = {"de": ["hallo","hi","hey","guten tag","guten morgen","guten abend"],
                 "en": ["hello","hi","hey","good morning","good evening"]}
    thanks = {"de": ["danke","vielen dank","merci","thx"], 
              "en": ["thanks","thank you","thx","cheers"]}
    farewells = {"de": ["tschüss","ciao","auf wiedersehen"], 
                 "en": ["bye","goodbye","see you"]}
    
    if any(word in q_lower for word in greetings[lang]):
        return random.choice(kb.get("begrüßung", kb.get("greeting", ["Hallo! Wie kann ich helfen?"])))
    if any(word in q_lower for word in thanks[lang]):
        return random.choice(kb.get("danke", kb.get("thanks", ["Gerne!"])))
    if any(word in q_lower for word in farewells[lang]):
        return random.choice(kb.get("verabschiedung", kb.get("farewell", ["Bis bald!"])))

    # -------------------------
    # 2️⃣ Öffnungszeiten & Unternehmensinfos
    # -------------------------
    if any(word in q_lower for word in ["öffnungszeiten","geöffnet","open","hours","geschäftszeiten","office hours"]):
        oh = kb.get("meta", {}).get("öffnungszeiten", kb.get("meta", {}).get("opening_hours", {}))
        today = datetime.datetime.now().strftime("%A").lower()
        # Aktueller Tag
        today_hours = oh.get(today, "geschlossen")
        # Alle Wochentage
        all_days = [f"{tag.title()}: {zeit}" for tag, zeit in oh.items() if tag not in ["aktuelle_öffnungszeiten","actual_opening_hours"]]
        return ("🕓 Öffnungszeiten heute:\n" + today_hours + "\n\n🕓 Öffnungszeiten Woche:\n" + "\n".join(all_days)) if lang=="de" else ("🕓 Opening hours today:\n" + today_hours + "\n\n🕓 Opening hours week:\n" + "\n".join(all_days))

    if "joel digitals" in q_lower and any(x in q_lower for x in ["wer","was","ist","who","what","unternehmen","company"]):
        u = kb.get("unternehmen", kb.get("company", {}))
        if lang=="de":
            return f"🏢 Joel Digitals – {u.get('beschreibung', u.get('description',''))}\n📍 Sitz: {u.get('sitz', u.get('headquarters',''))}\n🎯 Mission: {u.get('mission','')}"
        else:
            return f"🏢 Joel Digitals – {u.get('description','')}\n📍 Location: {u.get('headquarters','')}\n🎯 Mission: {u.get('mission','')}"

    # -------------------------
    # 3️⃣ Hilfe / Support
    # -------------------------
    help_keywords = {
        "de": ["hilfe", "support", "kontakt", "problem", "hilfe bekommen", "fragen", "beratung"],
        "en": ["help", "support", "contact", "problem", "faq", "assistance", "question"]
    }
    if any(word in q_lower for word in help_keywords[lang]):
        help_prod = kb.get("support") or kb.get("joel digitals support")
        if help_prod:
            desc = help_prod.get("beschreibung") or help_prod.get("description", "")
            url = help_prod.get("url") or help_prod.get("website") or "https://joel-digitals.de/contact"
            name = help_prod.get("name") or "Joel Digitals Support"
            return f"🆘 {name}\n{desc}\nWeitere Hilfe findest du unter: {url}"

    # -------------------------
    # 4️⃣ Produkt erkennen
    # -------------------------
    detected_products = []
    for key in PRODUCTS:
        prod = kb.get(key, {})
        prod_keywords = [key.lower()]
        if "name" in prod:
            prod_keywords.append(prod["name"].lower().replace(" ",""))
        prod_keywords += [kw.lower().replace(" ","") for kw in prod.get("keywords", [])]
        if any(kw in q_lower.replace(" ","") for kw in prod_keywords):
            detected_products.append(key)

    if not detected_products:
        detected = detect_product(q, kb)
        if detected:
            detected_products = [detected]
        elif (last := get_last_product()):
            detected_products = [last]

    # -------------------------
    # 5️⃣ Frageart erkennen
    # -------------------------
    wants_price = is_price_question(q_lower)
    wants_features = is_feature_question(q_lower)

    # -------------------------
    # 6️⃣ Antwort generieren
    # -------------------------
    for key in detected_products:
        prod = kb.get(key, {})
        name = prod.get("name", key)
        desc = prod.get("beschreibung") or prod.get("description", "")
        short = prod.get("kurz") or prod.get("short", "")
        
        # 🔹 Preis zuerst
        if wants_price and prod.get("preis") or prod.get("price"):
            preis = prod.get("preis") or prod.get("price")
            answers.append(f"💰 Preis für {name}: {preis}")
            continue

        # 🔹 Features
        if wants_features:
            feats = prod.get("features") or prod.get("services")
            if isinstance(feats, dict):
                lines = [f"• {k.capitalize()}: {v}" for k,v in feats.items()]
            elif isinstance(feats, list):
                lines = [f"• {x}" for x in feats]
            else:
                lines = ["Keine Funktionen verfügbar." if lang=="de" else "No features available."]
            answers.append(f"⚙️ Funktionen von {name}:\n" + "\n".join(lines))
            continue

        # 🔹 Standardbeschreibung
        if desc or short:
            answers.append(f"📘 {name}\n{desc}\n{short}")
    
    if not answers:
        return "Ich konnte dazu leider keine passenden Informationen finden." if lang=="de" else "I couldn't find matching information."
    
    final_answer = "\n\n".join(answers)
    remember_context(question, final_answer)
    return final_answer

def chatbot_answer(question, lang="de"):
    return generate_answer(question, lang)
