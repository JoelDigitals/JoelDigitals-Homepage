from django.db import migrations, models


def copy_title_description_forward(apps, schema_editor):
    AppIssue = apps.get_model('status', 'AppIssue')
    GlobalIssue = apps.get_model('status', 'GlobalIssue')
    for issue in AppIssue.objects.all():
        issue.title_de = issue.title
        issue.description_de = issue.description
        issue.save(update_fields=['title_de', 'description_de'])
    for issue in GlobalIssue.objects.all():
        issue.title_de = issue.title
        issue.description_de = issue.description
        issue.save(update_fields=['title_de', 'description_de'])


def copy_title_description_backward(apps, schema_editor):
    AppIssue = apps.get_model('status', 'AppIssue')
    GlobalIssue = apps.get_model('status', 'GlobalIssue')
    for issue in AppIssue.objects.all():
        issue.title = issue.title_de
        issue.description = issue.description_de
        issue.save(update_fields=['title', 'description'])
    for issue in GlobalIssue.objects.all():
        issue.title = issue.title_de
        issue.description = issue.description_de
        issue.save(update_fields=['title', 'description'])


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0002_appissue_resolved_at_appissue_severity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appissue',
            name='title_de',
            field=models.CharField(default='', max_length=200, verbose_name='Titel (DE)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='appissue',
            name='title_en',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Titel (EN)'),
        ),
        migrations.AddField(
            model_name='appissue',
            name='description_de',
            field=models.TextField(default='', verbose_name='Beschreibung (DE)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='appissue',
            name='description_en',
            field=models.TextField(blank=True, default='', verbose_name='Beschreibung (EN)'),
        ),
        migrations.AddField(
            model_name='globalissue',
            name='title_de',
            field=models.CharField(default='', max_length=200, verbose_name='Titel (DE)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='globalissue',
            name='title_en',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Titel (EN)'),
        ),
        migrations.AddField(
            model_name='globalissue',
            name='description_de',
            field=models.TextField(default='', verbose_name='Beschreibung (DE)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='globalissue',
            name='description_en',
            field=models.TextField(blank=True, default='', verbose_name='Beschreibung (EN)'),
        ),
        migrations.RunPython(copy_title_description_forward, copy_title_description_backward),
        migrations.RemoveField(model_name='appissue', name='title'),
        migrations.RemoveField(model_name='appissue', name='description'),
        migrations.RemoveField(model_name='globalissue', name='title'),
        migrations.RemoveField(model_name='globalissue', name='description'),
    ]
