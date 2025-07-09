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

    def __str__(self):
        return f"De {self.sender.username} à {self.recipient.username} le {self.created_at.strftime('%d/%m/%Y %H:%M')}"
