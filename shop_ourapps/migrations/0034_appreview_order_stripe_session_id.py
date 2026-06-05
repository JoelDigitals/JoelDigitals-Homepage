from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop_ourapps', '0033_order_delivered_at_order_registration_code_and_more'),
    ]

    operations = [
        # stripe_session_id on Order (fehlte im Model aber wird in views.py gesetzt)
        migrations.AddField(
            model_name='order',
            name='stripe_session_id',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        # AppReview model
        migrations.CreateModel(
            name='AppReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stars', models.PositiveSmallIntegerField(choices=[(0, '0 Sterne'), (1, '1 Stern'), (2, '2 Sterne'), (3, '3 Sterne'), (4, '4 Sterne'), (5, '5 Sterne')])),
                ('comment', models.TextField(max_length=500, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_approved', models.BooleanField(default=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='shop_ourapps.app')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='app_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('app', 'user')},
            },
        ),
    ]
