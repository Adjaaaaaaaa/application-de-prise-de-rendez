from django.contrib import admin
from .models import Seance

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'heure_debut', 'client', 'objet')
    list_filter = ('date',)
    search_fields = ('client__username', 'objet')
