from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

class Seance(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    objet = models.CharField(max_length=200)
    note_coach = models.TextField(blank=True, null=True)  # Non visible par client

    class Meta:
        unique_together = ['date', 'heure_debut']  # empêche les doublons
        ordering = ['-date', 'heure_debut']

    def __str__(self):
        return f"{self.date} {self.heure_debut} - {self.client.username}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    file = models.FileField(upload_to='messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"De {self.sender.username} à {self.recipient.username} le {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class Atelier(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    duree = models.CharField(max_length=100, blank=True, null=True)
    lieu = models.CharField(max_length=200, blank=True, null=True)
    tarif = models.DecimalField(max_digits=6, decimal_places=2)
    photo = models.ImageField(upload_to='ateliers/', blank=True, null=True)
    participants = models.ManyToManyField(User, related_name='ateliers_inscrits', blank=True)

    def __str__(self):
        return f"{self.titre} ({self.date})"

class Disponibilite(models.Model):
    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disponibilites')
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    restreint = models.BooleanField(default=False, help_text="Ce créneau est-il restreint (non réservable par les clients) ?")

    class Meta:
        verbose_name = 'Disponibilité'
        verbose_name_plural = 'Disponibilités'
        ordering = ['date', 'heure_debut']

    def __str__(self):
        return f"{self.coach} - {self.date} de {self.heure_debut} à {self.heure_fin}"

class Indisponibilite(models.Model):
    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='indisponibilites')
    TYPE_CHOICES = [
        ('jour', 'Jour entier'),
        ('creneau', 'Créneau précis'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    heure_debut = models.TimeField(blank=True, null=True)
    heure_fin = models.TimeField(blank=True, null=True)
    motif = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.type == 'jour':
            return f"Indispo {self.date_debut} (jour entier)"
        else:
            return f"Indispo {self.date_debut} {self.heure_debut}-{self.heure_fin}"
