from django.db import models
from django.contrib.auth.models import User

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
