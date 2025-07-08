from django import forms
from .models import Seance
from datetime import time, timedelta, datetime
from django.utils.timezone import now

class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = ['date', 'heure_debut', 'objet']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'objet': forms.TextInput(attrs={'placeholder': 'Objet de la séance'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        heure = cleaned_data.get("heure_debut")

        if date and heure:
            # bloquer si hors horaires
            if heure < time(9, 0) or heure > time(17, 0):
                raise forms.ValidationError("Horaires autorisés : 9h00 à 17h00")

            # empêcher le passé
            now_dt = datetime.now()
            seance_dt = datetime.combine(date, heure)
            if seance_dt < now_dt + timedelta(minutes=10):
                raise forms.ValidationError("Le rendez-vous doit être prévu au moins 10 minutes à l'avance")

            # vérifier les collisions
            if Seance.objects.filter(date=date, heure_debut=heure).exists():
                raise forms.ValidationError("Ce créneau est déjà pris.")
