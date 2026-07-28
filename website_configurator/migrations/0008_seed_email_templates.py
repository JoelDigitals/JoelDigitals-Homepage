from django.db import migrations

# (name, subject, body, sort_order)
TEMPLATES = [
    (
        'Rückfrage zu deiner Anfrage',
        'Rückfrage zu deiner Website-Anfrage {reference}',
        "Hallo {name},\n\n"
        "vielen Dank für deine Anfrage zu deiner neuen Website ({site_type}, {tech}).\n\n"
        "Um dir ein passendes Angebot machen zu können, hätten wir noch eine kurze Rückfrage:\n\n"
        "[Deine Frage hier]\n\n"
        "Viele Grüße\nJoel Digitals",
        0,
    ),
    (
        'Angebot folgt in Kürze',
        'Dein Angebot für deine neue Website ({reference})',
        "Hallo {name},\n\n"
        "vielen Dank für deine Anfrage! Wir haben deine Angaben geprüft und erstellen dir ein "
        "individuelles Angebot - das erhältst du in den nächsten Tagen von uns.\n\n"
        "Geschätzter Rahmen: {estimated_total}\n\n"
        "Viele Grüße\nJoel Digitals",
        1,
    ),
    (
        'Terminvorschlag',
        'Kurzes Gespräch zu deiner Website-Anfrage?',
        "Hallo {name},\n\n"
        "wir würden gerne kurz mit dir telefonieren, um ein paar Details zu deiner Anfrage "
        "({reference}) zu klären.\n\n"
        "Hast du diese Woche 15 Minuten Zeit? Gerne kannst du auch direkt einen Termin über "
        "unsere Website buchen.\n\n"
        "Viele Grüße\nJoel Digitals",
        2,
    ),
    (
        'Nachfassen (keine Rückmeldung)',
        'Kurzes Update zu deiner Website-Anfrage {reference}',
        "Hallo {name},\n\n"
        "wir wollten kurz nachfragen, ob du noch Interesse an deiner Website-Anfrage hast oder "
        "ob sich bei dir etwas geändert hat.\n\n"
        "Melde dich gerne, falls du noch Fragen hast!\n\n"
        "Viele Grüße\nJoel Digitals",
        3,
    ),
]


def seed(apps, schema_editor):
    EmailTemplate = apps.get_model('website_configurator', 'EmailTemplate')
    for name, subject, body, sort_order in TEMPLATES:
        EmailTemplate.objects.get_or_create(name=name, defaults={'subject': subject, 'body': body, 'sort_order': sort_order})


def unseed(apps, schema_editor):
    EmailTemplate = apps.get_model('website_configurator', 'EmailTemplate')
    EmailTemplate.objects.filter(name__in=[t[0] for t in TEMPLATES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('website_configurator', '0007_emailtemplate'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
