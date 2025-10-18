import json, os, datetime, re, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.json")
LEARN_FILE = os.path.join(BASE_DIR, "learned.json")

# Lade Knowledge
with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
    KNOWLEDGE = json.load(f)

# Lade Learned
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        try:
            LEARNED = json.load(f)
        except:
            LEARNED = {}
else:
    LEARNED = {}

def _normalize(text):
    return text.lower().strip() if isinstance(text, str) else ""

def _search_value(val, query_norm):
    results = []
    if isinstance(val, str):
        if query_norm in val.lower():
            results.append(val)
    elif isinstance(val, list):
        for item in val:
            results.extend(_search_value(item, query_norm))
    elif isinstance(val, dict):
        for v in val.values():
            results.extend(_search_value(v, query_norm))
    return results

def extract_keywords(question):
    return [w for w in re.findall(r'\w+', question) if len(w) > 3]

def lookup_database(keywords, lang="de"):
    kb = KNOWLEDGE.get(lang, KNOWLEDGE.get("de", {}))
    facts = []

    for kw in keywords:
        kw_norm = _normalize(kw)
        for key, val in kb.items():
            key_norm = _normalize(key).replace(" ", "_")
            if kw_norm in key_norm:
                # Wenn val ein Dict mit Beschreibung
                if isinstance(val, dict) and "beschreibung" in val:
                    facts.append(val["beschreibung"])
                # Wenn val String
                elif isinstance(val, str):
                    facts.append(val)
                # Wenn val Dict ohne Beschreibung
                elif isinstance(val, dict):
                    facts.append(str(val))

    # Duplikate entfernen
    return list(dict.fromkeys(facts))

def generate_answer(question, db_facts, lang="de"):
    kb = KNOWLEDGE.get(lang, KNOWLEDGE.get("de", {}))
    q_norm = _normalize(question)

    response_parts = []

    # 1. Begrüßung
    greetings = kb.get("begrüßung", ["Hallo!"])
    if any(w in q_norm for w in ["hi", "hallo", "hey"]):
        return random.choice(greetings)

    # 2. Verabschiedung
    farewells = kb.get("verabschiedung", ["Auf Wiedersehen!"])
    if any(w in q_norm for w in ["tschüss", "auf wiedersehen", "bye"]):
        return random.choice(farewells)

    # 3. Dank
    thanks = kb.get("danke", ["Danke!"])
    if any(w in q_norm for w in ["danke", "thank you"]):
        return random.choice(thanks)

    # 4. Prüfen auf bekannte Themen
    if "jds management" in q_norm or "jds" in q_norm:
        jds = kb.get("jds_management", {})
        text = f"{jds.get('beschreibung', '')}"
        if "docs" in jds:
            text += f" Weitere Informationen findest du hier: {jds['docs']}"
        response_parts.append(text)

    if "auftragnetz" in q_norm:
        auftrag = kb.get("auftragnetz", {})
        text = f"{auftrag.get('beschreibung', '')}"
        if "docs" in auftrag:
            text += f" Mehr Infos: {auftrag['docs']}"
        response_parts.append(text)

    if "öffnungszeiten" in q_norm or "opening hours" in q_norm:
        o = kb.get("meta", {}).get("öffnungszeiten", {})
        if o:
            today_hours = o.get("aktuelle_öffnungszeiten", "")
            response_parts.append(f"Die aktuellen Öffnungszeiten findest du hier: {today_hours}")

    if "kontakt" in q_norm or "email" in q_norm or "telefon" in q_norm:
        contact = kb.get("meta", {}).get("contact", "")
        email = kb.get("meta", {}).get("email", "")
        phone = kb.get("meta", {}).get("telefon", "")
        contact_text = f"Du kannst uns kontaktieren über die Seite {contact}"
        if email:
            contact_text += f" oder per E-Mail: {email}"
        if phone:
            contact_text += f", Telefon: {phone}"
        response_parts.append(contact_text)

    # 5. Wenn keine bekannten Themen gefunden
    if not response_parts:
        response_parts.append("Leider konnte ich dazu keine Informationen finden.")

    # 6. Antwort zusammenführen
    answer = " ".join(response_parts)

    # Learned speichern
    key = _normalize(question)
    if lang not in LEARNED:
        LEARNED[lang] = {}
    LEARNED[lang][key] = {"beschreibung": answer, "timestamp": datetime.datetime.now().isoformat()}
    with open(LEARN_FILE, "w", encoding="utf-8") as f:
        json.dump(LEARNED, f, ensure_ascii=False, indent=2)

    return answer


def chatbot_answer(question, lang="de"):
    keywords = extract_keywords(question)
    db_facts = lookup_database(keywords, lang)
    answer = generate_answer(question, db_facts, lang)

    # Speichern in learned.json (optional)
    key = _normalize(question)
    if lang not in LEARNED:
        LEARNED[lang] = {}
    LEARNED[lang][key] = {"beschreibung": answer, "timestamp": datetime.datetime.now().isoformat()}
    with open(LEARN_FILE, "w", encoding="utf-8") as f:
        json.dump(LEARNED, f, ensure_ascii=False, indent=2)

    return answer
