# Generated by Django 5.2.4 on 2025-07-08 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rdv_app', '0002_alter_seance_id_alter_seance_objet'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='seance',
            options={'ordering': ['-date', 'heure_debut']},
        ),
        migrations.RenameField(
            model_name='seance',
            old_name='heure',
            new_name='heure_debut',
        ),
        migrations.RenameField(
            model_name='seance',
            old_name='notes_coach',
            new_name='note_coach',
        ),
        migrations.AlterField(
            model_name='seance',
            name='objet',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='seance',
            unique_together={('date', 'heure_debut')},
        ),
    ]
