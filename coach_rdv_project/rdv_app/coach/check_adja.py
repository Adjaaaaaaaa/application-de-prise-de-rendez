#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_rdv_project.settings')
django.setup()

from django.contrib.auth.models import User
from rdv_app.models import Disponibilite, Seance, Indisponibilite

def check_system():
    """Vérifie l'état du système"""
    
    print("=== VÉRIFICATION DU SYSTÈME ===")
    
    # Vérifier l'utilisateur Adja
    try:
        adja = User.objects.get(username='adja')
        print(f"✅ Coach Adja trouvé : {adja.get_full_name() or adja.username}")
        print(f"   Email: {adja.email}")
        print(f"   Staff: {adja.is_staff}")
        print(f"   Active: {adja.is_active}")
    except User.DoesNotExist:
        print("❌ L'utilisateur 'adja' n'existe pas")
        print("Création de l'utilisateur Adja...")
        adja = User.objects.create_user(
            username='adja',
            email='adja@example.com',
            password='adja123',
            first_name='Adja',
            last_name='Coach',
            is_staff=True
        )
        print(f"✅ Coach Adja créé : {adja.username}")
    
    # Vérifier les disponibilités
    disponibilites = Disponibilite.objects.filter(coach=adja)
    print(f"📅 Disponibilités existantes : {disponibilites.count()}")
    
    # Vérifier les indisponibilités
    indisponibilites = Indisponibilite.objects.filter(coach=adja)
    print(f"🚫 Indisponibilités existantes : {indisponibilites.count()}")
    
    # Vérifier les rendez-vous
    seances = Seance.objects.all()
    print(f"📋 Rendez-vous existants : {seances.count()}")
    
    print("\n=== SYSTÈME PRÊT ===")
    print("Vous pouvez maintenant tester la prise de rendez-vous !")

if __name__ == '__main__':
    check_system() 