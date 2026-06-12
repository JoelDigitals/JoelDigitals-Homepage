# chat/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json, os, datetime
from .forms import TeachForm
from .bot_engine import chatbot_answer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.json")
LEARN_FILE = os.path.join(BASE_DIR, "learned.json")

# Lade Knowledge defensiv
with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
    KNOWLEDGE = json.load(f)

# Lehrdaten defensiv laden
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        try:
            LEARNED = json.load(f)
        except json.JSONDecodeError:
            LEARNED = {}
else:
    LEARNED = {}

def chat_response(request):
    """Einfacher Test-Endpunkt, ruft chatbot_answer auf"""
    user_input = request.POST.get("message", "")
    response = chatbot_answer(user_input)
    return JsonResponse({"response": response})


@csrf_exempt
def chatbot_api(request):
    """API-Endpunkt für Chatbot-Anfragen"""
    if request.method != "POST":
        return JsonResponse({"reply": "Bitte sende POST."})

    try:
        payload = json.loads(request.body)
        message = payload.get("message", "").strip()
        lang = payload.get("lang", "de")

        if not message:
            return JsonResponse({"reply": "Bitte schreibe etwas."})

        answer = chatbot_answer(message, lang)

        # Prüfe ob Transfer gewünscht / nötig
        transfer_to_human = "[TRANSFER]" in answer
        can_help = not transfer_to_human and "konnte nicht beantworten" not in answer and "could not answer" not in answer

        # Entferne Marker aus Antwort für Endnutzer
        clean_answer = answer.replace("[TRANSFER]", "")

        return JsonResponse({
            "reply": clean_answer,
            "transfer_to_human": transfer_to_human,
            "can_help": can_help,
        })
    except Exception as e:
        return JsonResponse({"reply": f"Fehler: {str(e)}"})


@csrf_exempt
def teach_api(request):
    """API-Endpunkt zum Hinzufügen neuen Wissens"""
    if request.method != "POST":
        return JsonResponse({"reply": "Bitte sende POST."})

    try:
        payload = json.loads(request.body)
        message = payload.get("message", "").strip()
        answer = payload.get("answer", "").strip()
        lang = payload.get("lang", "de")

        if not message or not answer:
            return JsonResponse({"reply": "Bitte Nachricht und Antwort angeben."})

        # Speichern in learned.json
        learned = {}
        if os.path.exists(LEARN_FILE):
            with open(LEARN_FILE, "r", encoding="utf-8") as fr:
                learned = json.load(fr)
        if lang not in learned:
            learned[lang] = {}
        learned[lang][message.lower()] = {
            "beschreibung": answer,
            "timestamp": datetime.datetime.now().isoformat()
        }
        with open(LEARN_FILE, "w", encoding="utf-8") as fw:
            json.dump(learned, fw, ensure_ascii=False, indent=2)

        return JsonResponse({"reply": "Erfolg! Das Wissen wurde gespeichert."})

    except Exception as e:
        return JsonResponse({"reply": f"Fehler: {str(e)}"})


def teach_page(request):
    """Admin-Seite zum Beibringen neuen Wissens"""
    success_msg = ""
    if request.method == "POST":
        form = TeachForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            answer = form.cleaned_data["answer"]
            lang = form.cleaned_data["lang"]

            # Speichern in learned.json
            learned = {}
            if os.path.exists(LEARN_FILE):
                with open(LEARN_FILE, "r", encoding="utf-8") as fr:
                    learned = json.load(fr)
            if lang not in learned:
                learned[lang] = {}
            learned[lang][message.lower()] = {
                "beschreibung": answer,
                "timestamp": datetime.datetime.now().isoformat()
            }
            with open(LEARN_FILE, "w", encoding="utf-8") as fw:
                json.dump(learned, fw, ensure_ascii=False, indent=2)

            success_msg = "Erfolg! Das Wissen wurde gespeichert."
            form = TeachForm()  # Reset form
    else:
        form = TeachForm()

    return render(request, "chat/teach_page.html", {"form": form, "success_msg": success_msg})
