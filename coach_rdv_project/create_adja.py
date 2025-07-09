#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_rdv_project.settings')
django.setup()

from django.contrib.auth.models import User

def create_adja():
    """Crée l'utilisateur Adja s'il n'existe pas"""
    
    try:
        adja = User.objects.get(username='adja')
        print(f"✅ L'utilisateur Adja existe déjà : {adja.get_full_name() or adja.username}")
    except User.DoesNotExist:
        print("Création de l'utilisateur Adja...")
        adja = User.objects.create_user(
            username='adja',
            email='adja@example.com',
            password='adja123',
            first_name='Adja',
            last_name='Coach',
            is_staff=True
        )
        print(f"✅ Utilisateur Adja créé avec succès !")
        print(f"   Username: {adja.username}")
        print(f"   Email: {adja.email}")
        print(f"   Mot de passe: adja123")
    
    print("\n🎉 Le coach Adja est maintenant disponible !")
    print("Les clients peuvent maintenant prendre rendez-vous.")

if __name__ == '__main__':
    create_adja() 