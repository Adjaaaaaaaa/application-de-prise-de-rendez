# 🗓️ Boost Carrière – Application de prise de rendez-vous en ligne

Application Django permettant à un coach en développement personnel de gérer ses séances avec ses clients. Les utilisateurs peuvent s’inscrire, se connecter et réserver un rendez-vous via une interface web moderne et intuitive.

---

## 🚀 Fonctionnalités principales

- Page d’accueil publique avec carrousel de témoignages
- Système d’inscription et d’authentification sécurisé (coach & client)
- Dashboard personnalisé :
  - **Coach** : accès à tous les rendez-vous, gestion des clients, messages, ateliers
  - **Client** : accès à ses propres rendez-vous, prise de RDV, gestion de profil
- Prise et modification de rendez-vous avec créneaux dynamiques
- Gestion des témoignages clients (validation par le coach, affichage public)
- Formulaire de contact
- Interface responsive et moderne
- Séparation stricte des espaces coach/client

---

## 📁 Structure du projet

```
application-de-prise-de-rendez/
├── coach_rdv_project/
│   ├── coach_rdv/                # Paramétrage principal du projet Django
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── rdv_app/                   # Application métier
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── migrations/
│   │   ├── static/
│   │   ├── templatetags/
│   │   └── templates/
│   ├── media/                     # Fichiers uploadés
│   ├── db.sqlite3                 # Base de données SQLite
│   └── manage.py                  # Commande de gestion Django
├── requirements.txt               # Dépendances Python
├── README.md                      # Documentation du projet
└── .venv/                         # Environnement virtuel Python

```

---

## ⚙️ Installation & Lancement

1. **Cloner le dépôt**
    ```bash
    git clone <url-du-repo>
    cd application-de-prise-de-rendez
    ```
2. **Créer un environnement virtuel** (recommandé)
    ```bash
    python -m venv .venv
    # Windows :
    .venv\Scripts\activate
    # macOS/Linux :
    source .venv/bin/activate
    ```
3. **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```
4. **Appliquer les migrations**
    ```bash
    python manage.py migrate
    ```
5. **Créer un superutilisateur** (pour l’admin coach)
    ```bash
    python manage.py createsuperuser
    ```
6. **Lancer le serveur de développement**
    ```bash
    python manage.py runserver
    ```
7. **Accéder à l’application**
    - [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🌐 URLs principales

| URL                | Description                        |
|--------------------|------------------------------------|
| `/`                | Page d’accueil                     |
| `/signup/`         | Inscription client                 |
| `/login/`          | Connexion                          |
| `/dashboard/`      | Espace client ou coach             |
| `/prendre-rdv/`    | Réserver une séance                |
| `/admin/`          | Interface admin (coach)            |

---

## 👥 Rôles utilisateurs

- **Coach (superuser)** :
  - Gère tous les rendez-vous, ateliers, messages, témoignages
  - Accès à l’interface `/admin/`
- **Client** :
  - Peut s’inscrire, se connecter
  - Réserve/modifie ses séances via l’interface
  - Peut déposer un témoignage

---

## 🔐 Sécurité & validations

- Authentification obligatoire pour accéder aux fonctionnalités sensibles
- Validation de la date (doit être future)
- Séparation stricte des vues coach/client
- Protection CSRF intégrée via Django
- Gestion des permissions via les groupes utilisateurs

---

## 💡 Pistes d’amélioration

- Ajout d’un calendrier visuel interactif
- Gestion avancée des créneaux horaires disponibles
- Notifications email ou SMS
- Rappels automatiques
- Ajout de commentaires ou comptes rendus de séances
- Statistiques avancées pour le coach

---

## 📦 Dépendances principales

Voir le fichier `requirements.txt` pour la liste complète.

---

## 🧪 Tests manuels

- Créer un superutilisateur
- S’inscrire avec un compte client
- Se connecter et tester la prise/modification de RDV
- Se connecter en tant que coach et voir tous les rendez-vous, messages, ateliers

---

## 📄 Licence

Ce projet est libre pour un usage personnel, éducatif ou professionnel.

---

**Contact** : Pour toute question ou suggestion, utilisez le formulaire de contact intégré à l’application.