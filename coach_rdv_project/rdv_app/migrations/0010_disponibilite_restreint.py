# Generated by Django 5.2.4 on 2025-07-09 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rdv_app', '0009_disponibilite'),
    ]

    operations = [
        migrations.AddField(
            model_name='disponibilite',
            name='restreint',
            field=models.BooleanField(default=False, help_text='Ce créneau est-il restreint (non réservable par les clients) ?'),
        ),
    ]
