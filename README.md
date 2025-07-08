# 🗓 Coach RDV – Application de prise de rendez-vous en ligne

Application Django permettant à un coach en développement personnel de gérer ses séances avec ses clients. Les utilisateurs peuvent s’inscrire, se connecter et réserver un rendez-vous via une interface web intuitive.

---

## ✅ Fonctionnalités

- Page d’accueil publique
- Système d’inscription et d’authentification sécurisé
- Dashboard personnalisé :
  - **Coach** : accès à tous les rendez-vous
  - **Client** : accès à ses propres rendez-vous uniquement
- Formulaire de réservation de séances
- Vérification que la date/heure est future
- Interface simple, extensible et responsive

---

## 📁 Structure du projet
``
application-de-prise-de-rendez/
├── coach_rdv/                # Dossier principal du projet (créé avec `django-admin startproject`)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── rdv_app/                  # app métier (créée avec `python manage.py startapp rdv_app`)
│   ├── migrations/
│   │   └── __init__.py
│   ├── templates/
│   │   └── rdv_app/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── dashboard_client.html
│   │       ├── dashboard_coach.html
│   │       └── prise_rdv.html
│   ├── static/               # (optionnel) CSS, JS, images propres à l'app
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py              # (optionnel) pour tes formulaires Django
│   ├── models.py             # Tes modèles (base de données)
│   ├── tests.py
│   └── views.py              # Tes vues
│
├── templates/                # (optionnel) Templates globaux, comme la page 404.html ou index.html
│
├── static/                   # (optionnel) Fichiers statiques globaux
│
├── media/                    # (optionnel) Fichiers uploadés (photos, docs, etc.)
│
├── db.sqlite3                # Fichier de base de données SQLite généré automatiquement
├── manage.py                 # Fichier de gestion Django
└── .venv/                    # Environnement virtuel Python
````



---

## ⚙️ Installation & Lancement
1. Cloner le dépôt :
    ```bash
    git clone https://github.com/ton-utilisateur/coach_rdv.git
    cd coach_rdv
    ```

2. Créer un environnement virtuel (optionnel mais recommandé) :
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows
    ```

3. Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

4. Appliquer les migrations :
    ```bash
    python manage.py migrate
    ```

5. Créer un super utilisateur (pour accéder à l’admin Django) :
    ```bash
    python manage.py createsuperuser
    ```

6. Lancer le serveur de développement :
    ```bash
    python manage.py runserver
    ```

7. Accéder à l’application dans un navigateur à l’adresse :
    ```
    http://127.0.0.1:8000/
    ```
---
## 🌐 Accès à l'application
URL	Description
/	Page d’accueil
/signup/	Inscription client
/login/	Connexion
/dashboard/	Espace client ou coach
/prendre-rdv/	Réserver une séance
/admin/	Interface admin (coach)

## 👥 Rôles utilisateurs
Coach (superuser) :

Gère tous les rendez-vous

Accès à l’interface /admin/

Client :

Peut s’inscrire, se connecter

Réserve des séances via l’interface

## 🔐 Sécurité et validations
Authentification obligatoire pour accéder aux fonctionnalités

Validation de la date (doit être future)

Séparation stricte des vues coach/client

CSRF intégré via Django

##💡 Pistes d'amélioration
Ajout d’un calendrier visuel

Gestion des créneaux horaires disponibles

Notifications email ou SMS

Rappels automatiques

Ajout de commentaires ou comptes rendus de séances

## 📦 Dépendances
Python 3.x

Django 4.x (ou supérieur)

Optionnel : Crée un fichier requirements.txt avec :

bash
Copier
Modifier
pip freeze > requirements.txt
🧪 Tests
Pour tester l'application manuellement :

Créer un superutilisateur

S’inscrire avec un compte client

Se connecter et tester la prise de RDV

Se connecter en tant que coach et voir tous les rendez-vous

📄 Licence
Ce projet est libre pour un usage personnel, éducatif ou professionnel.