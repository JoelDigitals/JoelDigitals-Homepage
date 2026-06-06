from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_ourapps', '0037_fix_missing_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='return_type',
            field=models.CharField(
                max_length=20,
                choices=[('refund', 'Rückerstattung'), ('exchange', 'Umtausch / Austausch')],
                default='refund',
                verbose_name='Art des Antrags',
            ),
        ),
    ]
