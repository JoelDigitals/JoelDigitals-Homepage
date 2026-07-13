from django.db import migrations


def backfill_forward(apps, schema_editor):
    """Markiert alle bereits veroeffentlichten Posts als 'schon benachrichtigt',
    damit der neue Push-Cron-Check sie nicht rueckwirkend als 'neu' meldet."""
    BlogPost = apps.get_model('blog', 'BlogPost')
    BlogPost.objects.filter(
        is_published=True, published_at__isnull=False, push_notified_at__isnull=True
    ).update(push_notified_at=models_f())


def models_f():
    from django.db.models import F
    return F('published_at')


def backfill_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_blogpost_push_notified_at'),
    ]

    operations = [
        migrations.RunPython(backfill_forward, backfill_backward),
    ]
