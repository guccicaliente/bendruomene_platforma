# Generated by Django 5.2 on 2025-05-01 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_add_topic_to_vote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='votingtopic',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='Pabaigos data'),
        ),
    ]
