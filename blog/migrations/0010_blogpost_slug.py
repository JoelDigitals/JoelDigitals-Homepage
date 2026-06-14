from django.db import migrations, models
from django.utils.text import slugify


def gen_slugs(apps, schema_editor):
    BlogPost = apps.get_model('blog', 'BlogPost')
    for post in BlogPost.objects.all():
        base = post.title_de
        slug = slugify(base) or f"post-{post.pk}"
        n = 1
        orig = slug
        while BlogPost.objects.filter(slug=slug).exclude(pk=post.pk).exists():
            slug = f"{orig}-{n}"
            n += 1
        post.slug = slug
        post.save(update_fields=['slug'])


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0009_blogviewtracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(max_length=250, blank=True, default='', verbose_name='Slug'),
            preserve_default=False,
        ),
        migrations.RunPython(gen_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(max_length=250, unique=True, blank=True, verbose_name='Slug'),
        ),
    ]
