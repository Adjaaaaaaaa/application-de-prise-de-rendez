from django import forms
from .models import Seance, Profile, Message, Disponibilite, Indisponibilite, Atelier, Temoinage
from datetime import time, timedelta, datetime
from django.utils.timezone import now
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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

class SignupForm(UserCreationForm):
    first_name = forms.CharField(label='Prénom', required=True)
    last_name = forms.CharField(label='Nom', required=True)
    email = forms.EmailField(required=True, label='Adresse email', widget=forms.EmailInput(attrs={'placeholder': 'Votre email'}))
    telephone = forms.CharField(required=False, label='Téléphone (facultatif)', widget=forms.TextInput(attrs={'placeholder': 'Votre téléphone'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Création ou mise à jour du profil pour le téléphone
            from .models import Profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.telephone = self.cleaned_data['telephone']
            profile.save()
        return user

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Adresse email', required=True)

    class Meta:
        model = Profile
        fields = ['telephone']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email

    def save(self, user, commit=True):
        profile = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile

class ProfileFullForm(forms.ModelForm):
    first_name = forms.CharField(label='Prénom', required=True)
    last_name = forms.CharField(label='Nom', required=True)
    email = forms.EmailField(label='Adresse email', required=True)

    class Meta:
        model = Profile
        fields = ['telephone']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        self.user = user

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = self.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Votre message...'}),
        }

class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ['date', 'heure_debut', 'heure_fin', 'restreint']

class IndisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Indisponibilite
        fields = ['type', 'date_debut', 'date_fin', 'heure_debut', 'heure_fin', 'motif']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

class AtelierForm(forms.ModelForm):
    class Meta:
        model = Atelier
        fields = ['titre', 'description', 'date', 'duree', 'nombre_maximal', 'lieu', 'tarif', 'photo']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': "Description de l'atelier"}),
            'duree': forms.TextInput(attrs={'placeholder': 'Durée (ex: 2h)'}),
            'lieu': forms.TextInput(attrs={'placeholder': "Lieu de l'atelier"}),
            'tarif': forms.NumberInput(attrs={'min': 0, 'step': 1, 'placeholder': 'Tarif en €'}),
            'nombre_maximal': forms.NumberInput(attrs={'min': 1, 'step': 1, 'placeholder': 'Nombre maximal de participants'}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if not photo.content_type in ['image/jpeg', 'image/png']:
                raise forms.ValidationError('Format de photo non supporté. Utilisez jpg ou png.')
            if photo.size > 2*1024*1024:
                raise forms.ValidationError('La taille de la photo ne doit pas dépasser 2 Mo.')
        return photo

    def clean_lieu(self):
        lieu = self.cleaned_data.get('lieu')
        if not lieu:
            raise forms.ValidationError('Le lieu est obligatoire.')
        return lieu

    def clean_nombre_maximal(self):
        nombre = self.cleaned_data.get('nombre_maximal')
        if nombre is not None and nombre < 1:
            raise forms.ValidationError('Le nombre de places doit être au moins 1.')
        return nombre

class TemoinageForm(forms.ModelForm):
    class Meta:
        model = Temoinage
        fields = ['texte', 'profession']
        widgets = {
            'texte': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Votre témoignage...'}),
            'profession': forms.TextInput(attrs={'placeholder': 'Votre profession (ex: Ingénieur, Étudiant...)'}),
        }
