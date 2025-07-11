from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Seance, Profile, Message, Atelier, Temoinage
from .forms import SeanceForm, SignupForm, ProfileForm, ProfileFullForm, MessageForm, TemoinageForm
from datetime import date
from django.contrib import messages
from django.db import models
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.utils import timezone

class AtelierForm(forms.ModelForm):
    class Meta:
        model = Atelier
        fields = ['titre', 'description', 'date', 'tarif']

def mark_messages_as_read(user, other_user):
    """Marque tous les messages d'un utilisateur comme lus"""
    from .models import Message
    try:
        Message.objects.filter(sender=other_user, recipient=user, lu=False).update(lu=True)
    except:
        # Si le champ 'lu' n'existe pas encore, ne rien faire
        pass

def get_unread_messages_count(user):
    """Compte les messages non lus pour un utilisateur"""
    from .models import Message
    try:
        # Vérifier si le champ 'lu' existe (après migration)
        unread_count = Message.objects.filter(recipient=user, lu=False).count()
        # Si tous les messages sont marqués comme non lus (anciens messages), les marquer comme lus
        total_messages = Message.objects.filter(recipient=user).count()
        if unread_count == total_messages and total_messages > 0:
            Message.objects.filter(recipient=user).update(lu=True)
            return 0
        return unread_count
    except:
        # Si le champ 'lu' n'existe pas encore, retourner 0
        return 0

def add_notifications_to_context(context, user):
    """Ajoute le nombre de messages non lus au contexte"""
    if user.is_authenticated:
        context['unread_messages'] = get_unread_messages_count(user)
    return context

def accueil(request):
    import random
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    from .models import Temoinage
    temoignages = list(Temoinage.objects.filter(valide=True).order_by('-date'))
    # On veut toujours un multiple de 3 pour le carrousel
    n = len(temoignages)
    if n == 0:
        temoignages_display = []
    else:
        # On limite à 6 ou plus si besoin
        max_display = 6 if n >= 6 else n
        temoignages_display = temoignages[:max_display]
        # Compléter pour avoir un multiple de 3
        reste = (3 - len(temoignages_display) % 3) % 3
        if reste:
            # On complète avec des témoignages aléatoires (avec répétition possible)
            temoignages_display += random.choices(temoignages, k=reste)
    context = {'is_coach': is_coach, 'temoignages_display': temoignages_display}
    context = add_notifications_to_context(context, request.user)
    if request.user.is_authenticated:
        return render(request, 'rdv_app/accueil_public.html', context)
    return render(request, 'rdv_app/accueil.html', context)

def choix_auth_view(request):
    """Page de choix entre connexion et inscription"""
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    context = {'is_coach': is_coach}
    context = add_notifications_to_context(context, request.user)
    return render(request, 'rdv_app/choix_auth.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Affecter au groupe "client" automatiquement
            group, created = Group.objects.get_or_create(name='client')
            user.groups.add(group)
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = SignupForm()
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/signup.html', {'form': form, 'is_coach': is_coach})

from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'rdv_app/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and (user.groups.filter(name='coach').exists() or user.username.lower() == 'adja'):
            return '/coach/calendrier/'
        return super().get_success_url()

@login_required
def dashboard(request):
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    if is_coach:
        seances = Seance.objects.all().order_by('date', 'heure_debut')
        # Statistiques coach
        nb_clients = Seance.objects.values('client').distinct().count()
        nb_seances = Seance.objects.count()
        gain_total = nb_seances * 49  # 49€ par séance
        today = date.today()
        programme_jour = Seance.objects.filter(date=today).order_by('heure_debut')
        template = 'rdv_app/dashboard_coach.html'
        context = {
            'seances': seances,
            'nb_clients': nb_clients,
            'nb_seances': nb_seances,
            'gain_total': gain_total,
            'programme_jour': programme_jour,
        }
    else:
        from datetime import datetime
        now = datetime.now()
        seances_avenir = Seance.objects.filter(client=request.user, date__gte=now.date()).order_by('date', 'heure_debut')
        seances_passees = Seance.objects.filter(client=request.user, date__lt=now.date()).order_by('-date', '-heure_debut')
        template = 'rdv_app/dashboard_client.html'
        context = {'seances_avenir': seances_avenir, 'seances_passees': seances_passees}
    context['is_coach'] = is_coach
    context = add_notifications_to_context(context, request.user)
    return render(request, template, context)
    
@login_required
def dashboard_coach_view(request):
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    
    from .models import Atelier, Seance, Message, Temoinage
    from datetime import datetime, date
    from calendar import monthrange
    
    # Statistiques de base
    nb_ateliers = Atelier.objects.count()
    nb_clients = Seance.objects.values('client').distinct().count()
    nb_messages = Message.objects.filter(recipient=request.user).count()
    nb_temoignages = Temoinage.objects.count()
    
    # Calcul des gains par mois
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Gains des rendez-vous du mois en cours
    # Tarifs selon le type de consultation
    tarifs_consultation = {
        'premiere': 49,  # Première consultation
        'coaching': 120,  # Coaching individuel
        'motivation': 120,  # Suivi motivationnel
        'bilan': 120,  # Bilan de compétences
    }
    
    # Rendez-vous du mois en cours
    seances_mois = Seance.objects.filter(
        date__year=current_year,
        date__month=current_month
    )
    
    gains_rdv_mois = 0
    for seance in seances_mois:
        # Déterminer le type de consultation basé sur l'objet
        objet = seance.objet.lower()
        if 'première' in objet or 'premiere' in objet:
            gains_rdv_mois += tarifs_consultation['premiere']
        else:
            # Pour les autres types, utiliser le tarif standard
            gains_rdv_mois += tarifs_consultation['coaching']
    
    # Gains des ateliers du mois en cours
    ateliers_mois = Atelier.objects.filter(
        date__year=current_year,
        date__month=current_month
    )
    
    gains_ateliers_mois = 0
    nb_participants_mois = 0
    for atelier in ateliers_mois:
        nb_participants = atelier.participants.count()
        gains_ateliers_mois += atelier.tarif * nb_participants
        nb_participants_mois += nb_participants
    
    # Total des gains du mois
    gains_total_mois = gains_rdv_mois + gains_ateliers_mois
    
    # Statistiques du mois précédent pour comparaison
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
    
    seances_mois_prec = Seance.objects.filter(
        date__year=prev_year,
        date__month=prev_month
    )
    
    gains_rdv_mois_prec = 0
    for seance in seances_mois_prec:
        objet = seance.objet.lower()
        if 'première' in objet or 'premiere' in objet:
            gains_rdv_mois_prec += tarifs_consultation['premiere']
        else:
            gains_rdv_mois_prec += tarifs_consultation['coaching']
    
    ateliers_mois_prec = Atelier.objects.filter(
        date__year=prev_year,
        date__month=prev_month
    )
    
    gains_ateliers_mois_prec = 0
    for atelier in ateliers_mois_prec:
        nb_participants = atelier.participants.count()
        gains_ateliers_mois_prec += atelier.tarif * nb_participants
    
    gains_total_mois_prec = gains_rdv_mois_prec + gains_ateliers_mois_prec
    
    # Évolution en pourcentage
    if gains_total_mois_prec > 0:
        evolution_pct = ((gains_total_mois - gains_total_mois_prec) / gains_total_mois_prec) * 100
    else:
        evolution_pct = 0
    
    # Calcul des moyennes
    nb_rdv_mois = seances_mois.count()
    nb_ateliers_mois = ateliers_mois.count()
    
    gain_moyen_rdv = 0
    if nb_rdv_mois > 0:
        gain_moyen_rdv = gains_rdv_mois / nb_rdv_mois
    
    # Calcul du nombre d'heures travaillées dans le mois
    total_minutes = 0
    for seance in seances_mois:
        objet = seance.objet.lower()
        if 'première' in objet or 'premiere' in objet:
            total_minutes += 30
        else:
            total_minutes += 120
    heures_travaillees_mois = total_minutes // 60
    minutes_restantes = total_minutes % 60
    
    is_coach = True
    return render(request, 'rdv_app/dashboard_coach.html', {
        'nb_ateliers': nb_ateliers,
        'nb_clients': nb_clients,
        'nb_temoignages': nb_temoignages,
        'gains_rdv_mois': gains_rdv_mois,
        'gains_ateliers_mois': gains_ateliers_mois,
        'gains_total_mois': gains_total_mois,
        'gains_total_mois_prec': gains_total_mois_prec,
        'evolution_pct': evolution_pct,
        'nb_participants_mois': nb_participants_mois,
        'nb_rdv_mois': nb_rdv_mois,
        'nb_ateliers_mois': nb_ateliers_mois,
        'heures_travaillees_mois': heures_travaillees_mois,
        'minutes_restantes': minutes_restantes,
        'current_month': current_month,
        'current_year': current_year,
        'is_coach': is_coach,
    })

def prendre_rdv(request):
    # Vérifier si l'utilisateur est connecté
    if not request.user.is_authenticated:
        return redirect('choix_auth')
    
    print("DEBUG: Début de la vue prendre_rdv")  # Debug
    from .models import Disponibilite, Seance, Indisponibilite
    from datetime import datetime, time, timedelta
    from django.utils import timezone
    
    print(f"DEBUG: Utilisateur connecté = {request.user.username}")  # Debug
    print(f"DEBUG: is_coach = {request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')}")  # Debug
    
    # Récupérer les créneaux déjà réservés
    creneaux_reserves = Seance.objects.values_list('date', 'heure_debut')
    print(f"DEBUG: {len(creneaux_reserves)} créneaux déjà réservés")  # Debug
    
    # Récupérer les indisponibilités du coach (utilisateur staff)
    from django.contrib.auth.models import User
    coach = User.objects.filter(is_staff=True).first()
    print(f"DEBUG: Coach trouvé = {coach.username if coach else 'Aucun'}")  # Debug
    
    if not coach:
        print("DEBUG: Aucun coach trouvé, redirection vers dashboard")  # Debug
        messages.error(request, 'Aucun coach disponible.')
        return redirect('dashboard')
    
    indisponibilites = Indisponibilite.objects.filter(coach=coach)
    print(f"DEBUG: {indisponibilites.count()} indisponibilités trouvées")  # Debug
    
    # Types de consultation avec leurs durées
    types_consultation = [
        ('premiere', 'Première consultation', 30),
        ('coaching', 'Coaching individuel', 120),
        ('motivation', 'Suivi motivationnel', 120),
        ('bilan', 'Bilan de compétences', 120)
    ]
    
    # Récupérer le type de consultation sélectionné
    type_selectionne = request.GET.get('type', 'premiere')
    duree_minutes = next((duree for type_id, nom, duree in types_consultation if type_id == type_selectionne), 30)
    
    # Créer des créneaux virtuels pour les prochains jours (disponibilité par défaut)
    today = timezone.now().date()
    creneaux_disponibles = []
    
    # Créneaux horaires de base (débuts possibles)
    if duree_minutes == 30:
        # Pour 30 min : créneaux toutes les 30 min
        horaires_debut = [
            time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30),
            time(14, 0), time(14, 30), time(15, 0), time(15, 30), time(16, 0), time(16, 30)
        ]
    else:
        # Pour 2h : créneaux toutes les heures
        horaires_debut = [
            time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0)
        ]
    
    print(f"DEBUG: Génération des créneaux pour {today} - Durée: {duree_minutes} min")  # Debug
    
    # Générer les créneaux pour les 14 prochains jours
    for i in range(14):
        date = today + timedelta(days=i)
        
        # Exclure les weekends
        if date.weekday() >= 5:  # Samedi=5, Dimanche=6
            continue
            
        for heure_debut in horaires_debut:
            # Calculer l'heure de fin
            heure_fin = (datetime.combine(date, heure_debut) + timedelta(minutes=duree_minutes)).time()
            
            # Vérifier que le créneau ne dépasse pas 17h00
            if heure_fin > time(17, 0):
                continue
            
            # Vérifier si le créneau n'est pas déjà réservé
            creneau_reserve = False
            for creneau_date, creneau_heure in creneaux_reserves:
                if creneau_date == date:
                    # Vérifier si le créneau chevauche
                    creneau_fin = (datetime.combine(creneau_date, creneau_heure) + timedelta(minutes=60)).time()
                    if not (heure_fin <= creneau_heure or heure_debut >= creneau_fin):
                        creneau_reserve = True
                        break
            
            if not creneau_reserve:
                # Vérifier si le créneau n'est pas dans une indisponibilité
                creneau_disponible = True
                
                for indispo in indisponibilites:
                    if indispo.type == 'jour':
                        # Indisponibilité jour entier
                        if indispo.date_debut <= date <= (indispo.date_fin or indispo.date_debut):
                            creneau_disponible = False
                            break
                    else:
                        # Indisponibilité créneau précis
                        if (indispo.date_debut <= date <= (indispo.date_fin or indispo.date_debut) and
                            indispo.heure_debut and indispo.heure_fin):
                            # Vérifier si le créneau chevauche l'indisponibilité
                            if not (heure_fin <= indispo.heure_debut or heure_debut >= indispo.heure_fin):
                                creneau_disponible = False
                                break
                
                if creneau_disponible:
                    creneaux_disponibles.append({
                        'date': date,
                        'heure_debut': heure_debut,
                        'heure_fin': heure_fin,
                        'duree': duree_minutes,
                        'duree_nom': f"{duree_minutes} min" if duree_minutes == 30 else f"{duree_minutes//60}h",
                        'id': f"virtuel_{date}_{heure_debut.hour}_{heure_debut.minute}_{duree_minutes}"
                    })
    
    print(f"DEBUG: {len(creneaux_disponibles)} créneaux disponibles générés")  # Debug
    
    if request.method == 'POST':
        print("DEBUG: Méthode POST détectée")  # Debug
        creneau_id = request.POST.get('creneau')
        type_consultation = request.POST.get('type_consultation', 'premiere')
        print(f"DEBUG: creneau_id reçu = {creneau_id}")  # Debug
        print(f"DEBUG: type_consultation = {type_consultation}")  # Debug
        
        if creneau_id and creneau_id.startswith('virtuel_'):
            try:
                # Extraire les informations du créneau virtuel
                parts = creneau_id.split('_')
                print(f"DEBUG: parts = {parts}")  # Debug
                
                if len(parts) >= 5:
                    date_str = parts[1]
                    heure_h = int(parts[2])
                    heure_m = int(parts[3])
                    duree = int(parts[4])
                    
                    print(f"DEBUG: date_str={date_str}, heure_h={heure_h}, heure_m={heure_m}, duree={duree}")  # Debug
                    
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    heure_obj = time(heure_h, heure_m)
                    
                    print(f"DEBUG: date_obj={date_obj}, heure_obj={heure_obj}")  # Debug
                    
                    # Vérifier une dernière fois que le créneau est disponible
                    if not Seance.objects.filter(date=date_obj, heure_debut=heure_obj).exists():
                        # Trouver le nom du type de consultation
                        nom_consultation = next((nom for type_id, nom, d in types_consultation if type_id == type_consultation), 'Consultation')
                        
                        seance = Seance.objects.create(
                            client=request.user,
                            date=date_obj,
                            heure_debut=heure_obj,
                            objet=f"{nom_consultation} ({duree} min)"
                        )
                        messages.success(request, f'Rendez-vous réservé le {date_obj.strftime("%d/%m/%Y")} à {heure_obj.strftime("%H:%M")} - {nom_consultation}')
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'Ce créneau a déjà été réservé.')
                else:
                    messages.error(request, 'Format de créneau invalide.')
            except Exception as e:
                print(f"DEBUG: Erreur lors du traitement = {e}")  # Debug
                messages.error(request, f'Erreur lors de la réservation : {str(e)}')
        else:
            print(f"DEBUG: creneau_id invalide ou manquant")  # Debug
            messages.error(request, 'Veuillez sélectionner un créneau valide.')
    
    print("DEBUG: Rendu du template")  # Debug
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/prise_rdv.html', {
        'creneaux_disponibles': creneaux_disponibles, 
        'types_consultation': types_consultation,
        'type_selectionne': type_selectionne,
        'is_coach': is_coach
    })

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/profile.html', {
        'profile': profile,
        'user_obj': request.user,
        'show_update_btn': True,
        'is_coach': is_coach,
    })

@login_required
def profile_update_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, 'Votre profil a bien été mis à jour.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/profile_update.html', {'form': form, 'profile': profile, 'user_obj': request.user, 'is_coach': is_coach})

@login_required
def seance_update_view(request, pk):
    from .models import Seance, Indisponibilite
    from datetime import datetime, time, timedelta
    from django.utils import timezone
    from django.contrib.auth.models import User
    seance = get_object_or_404(Seance, pk=pk)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    if not (request.user == seance.client or is_coach):
        return redirect('dashboard')

    # Types de consultation avec leurs durées
    types_consultation = [
        ('premiere', 'Première consultation', 30),
        ('coaching', 'Coaching individuel', 120),
        ('motivation', 'Suivi motivationnel', 120),
        ('bilan', 'Bilan de compétences', 120)
    ]
    # Déterminer le type sélectionné (POST, GET, ou valeur actuelle)
    type_selectionne = request.POST.get('type') or request.GET.get('type')
    if not type_selectionne:
        # Déduire à partir de l'objet du rendez-vous
        obj = seance.objet.lower()
        if 'première' in obj or 'premiere' in obj:
            type_selectionne = 'premiere'
        elif 'coaching' in obj:
            type_selectionne = 'coaching'
        elif 'motivation' in obj:
            type_selectionne = 'motivation'
        elif 'bilan' in obj:
            type_selectionne = 'bilan'
        else:
            type_selectionne = 'premiere'
    duree_minutes = next((duree for type_id, nom, duree in types_consultation if type_id == type_selectionne), 30)

    # Générer les créneaux disponibles (hors celui du rendez-vous actuel)
    coach = seance.client if is_coach else None
    if not coach:
        coach = User.objects.filter(username='adja').first() or User.objects.filter(is_staff=True).first()
    indisponibilites = Indisponibilite.objects.filter(coach=coach)
    creneaux_reserves = Seance.objects.exclude(pk=seance.pk).values_list('date', 'heure_debut')

    # Créneaux horaires de base
    if duree_minutes == 30:
        horaires_debut = [
            time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30),
            time(14, 0), time(14, 30), time(15, 0), time(15, 30), time(16, 0), time(16, 30)
        ]
    else:
        horaires_debut = [
            time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0)
        ]

    today = timezone.now().date()
    creneaux_disponibles = []
    for i in range(14):
        date_jour = today + timedelta(days=i)
        if date_jour.weekday() >= 5:
            continue
        for heure_debut in horaires_debut:
            heure_fin = (datetime.combine(date_jour, heure_debut) + timedelta(minutes=duree_minutes)).time()
            if heure_fin > time(17, 0):
                continue
            # Vérifier si le créneau est réservé
            creneau_reserve = any(cd == date_jour and ch == heure_debut for cd, ch in creneaux_reserves)
            if creneau_reserve:
                continue
            # Vérifier indisponibilités
            creneau_disponible = True
            for indispo in indisponibilites:
                if indispo.type == 'jour':
                    if indispo.date_debut <= date_jour <= (indispo.date_fin or indispo.date_debut):
                        creneau_disponible = False
                        break
                else:
                    if (indispo.date_debut <= date_jour <= (indispo.date_fin or indispo.date_debut) and indispo.heure_debut and indispo.heure_fin):
                        if not (heure_fin <= indispo.heure_debut or heure_debut >= indispo.heure_fin):
                            creneau_disponible = False
                            break
            if creneau_disponible:
                creneaux_disponibles.append({
                    'date': date_jour,
                    'heure_debut': heure_debut,
                    'heure_fin': heure_fin,
                    'duree': duree_minutes,
                    'duree_nom': f"{duree_minutes} min" if duree_minutes == 30 else f"{duree_minutes//60}h",
                    'id': f"virtuel_{date_jour}_{heure_debut.hour}_{heure_debut.minute}_{duree_minutes}"
                })
    # Ajouter le créneau actuel même s'il n'est plus dispo
    id_actuel = f"virtuel_{seance.date}_{seance.heure_debut.hour}_{seance.heure_debut.minute}_{duree_minutes}"
    if not any(c['id'] == id_actuel for c in creneaux_disponibles):
        heure_fin = (datetime.combine(seance.date, seance.heure_debut) + timedelta(minutes=duree_minutes)).time()
        creneaux_disponibles.append({
            'date': seance.date,
            'heure_debut': seance.heure_debut,
            'heure_fin': heure_fin,
            'duree': duree_minutes,
            'duree_nom': f"{duree_minutes} min" if duree_minutes == 30 else f"{duree_minutes//60}h",
            'id': id_actuel
        })

    # Gestion du POST
    if request.method == 'POST' and 'creneau' in request.POST:
        creneau_id = request.POST.get('creneau')
        type_consultation = request.POST.get('type')
        if creneau_id and creneau_id.startswith('virtuel_'):
            try:
                parts = creneau_id.split('_')
                if len(parts) >= 5:
                    date_str = parts[1]
                    heure_h = int(parts[2])
                    heure_m = int(parts[3])
                    duree = int(parts[4])
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    heure_obj = time(heure_h, heure_m)
                    # Vérifier une dernière fois que le créneau est disponible
                    if not Seance.objects.filter(date=date_obj, heure_debut=heure_obj).exclude(pk=seance.pk).exists():
                        nom_consultation = next((nom for type_id, nom, d in types_consultation if type_id == type_consultation), 'Consultation')
                        seance.date = date_obj
                        seance.heure_debut = heure_obj
                        seance.objet = nom_consultation
                        seance.save()
                        messages.success(request, f'Rendez-vous modifié pour le {date_obj.strftime("%d/%m/%Y")} à {heure_obj.strftime("%H:%M")} - {nom_consultation}')
                        return redirect('calendrier_coach')
                    else:
                        messages.error(request, 'Ce créneau a déjà été réservé.')
                else:
                    messages.error(request, 'Format de créneau invalide.')
            except Exception as e:
                messages.error(request, f'Erreur lors de la modification : {str(e)}')
        else:
            messages.error(request, 'Veuillez sélectionner un créneau valide.')

    return render(request, 'rdv_app/seance_update.html', {
        'seance': seance,
        'types_consultation': types_consultation,
        'type_selectionne': type_selectionne,
        'creneaux_disponibles': creneaux_disponibles,
        'is_coach': is_coach
    })

@login_required
def seance_delete_view(request, pk):
    from django.core.mail import send_mail
    seance = get_object_or_404(Seance, pk=pk)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    # Seul le client ou le coach peut annuler
    if not (request.user == seance.client or is_coach):
            return redirect('dashboard')
    if request.method == 'POST':
        client = seance.client
        # Identifier le coach (supposons que c'est l'utilisateur 'adja' ou un staff)
        from django.contrib.auth.models import User
        coach = User.objects.filter(username='adja').first() or User.objects.filter(is_staff=True).first()
        
        if is_coach:
            # Coach annule → notifier le client
            Message.objects.create(
                sender=request.user,
                recipient=client,
                content=f"Votre rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')} a été annulé par le coach."
            )
            send_mail(
                subject="Annulation de votre rendez-vous Boost Carrière",
                message=f"Bonjour {client.first_name},\n\nVotre rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')} a été annulé par le coach. N'hésitez pas à reprendre rendez-vous sur la plateforme.\n\nCordialement,\nBoost Carrière",
                from_email=None,
                recipient_list=[client.email],
                fail_silently=True,
            )
            messages.success(request, 'Le rendez-vous a bien été annulé et le client a été notifié.')
        else:
            # Client annule → notifier le coach
            Message.objects.create(
                sender=request.user,
                recipient=coach,
                content=f"Le client {client.get_full_name()} a annulé son rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')}."
            )
            send_mail(
                subject="Annulation de rendez-vous par le client",
                message=f"Bonjour,\n\nLe client {client.get_full_name()} ({client.email}) a annulé son rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')}.\n\nCordialement,\nBoost Carrière",
                from_email=None,
                recipient_list=[coach.email],
                fail_silently=True,
            )
            messages.success(request, 'Votre rendez-vous a bien été annulé et le coach a été notifié.')
        
        seance.delete()
        return redirect('calendrier_coach')
    return render(request, 'rdv_app/seance_confirm_delete.html', {'seance': seance, 'is_coach': is_coach})

@login_required
def messages_view(request):
    from django.contrib.auth.models import User
    coach = User.objects.filter(is_staff=True).first() or User.objects.filter(username='adja').first()
    # Liste des discussions (ici, un seul fil avec le coach)
    discussions = [{'id': coach.id, 'name': coach.get_full_name() or coach.username}]
    selected_id = request.GET.get('discussion', coach.id)
    show_new = request.GET.get('new', None)
    # Fil de discussion sélectionné
    messages_list = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(recipient=coach)) |
        (models.Q(sender=coach) & models.Q(recipient=request.user))
    ).order_by('created_at')
    # Marquer les messages du coach comme lus
    mark_messages_as_read(request.user, coach)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = coach
            msg.save()
            return redirect('messages')
    else:
        form = MessageForm()
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    context = {
        'form': form,
        'messages_list': messages_list,
        'coach': coach,
        'discussions': discussions,
        'selected_id': int(selected_id) if selected_id else coach.id,
        'show_new': show_new,
        'is_coach': is_coach,
    }
    context = add_notifications_to_context(context, request.user)
    return render(request, 'rdv_app/messages.html', context)

@login_required
def messages_coach_view(request):
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from django.contrib.auth.models import User
    from .models import Message, ContactMessage
    # Suppression d'un message de contact externe
    if request.method == 'POST' and 'delete_contact_id' in request.POST:
        contact_id = request.POST.get('delete_contact_id')
        ContactMessage.objects.filter(id=contact_id).delete()
        return redirect(request.path)
    # Suppression d'une discussion avec un client
    if request.method == 'POST' and 'delete_discussion_id' in request.POST:
        client_id = request.POST.get('delete_discussion_id')
        Message.objects.filter(
            (models.Q(sender_id=client_id) & models.Q(recipient=request.user)) |
            (models.Q(sender=request.user) & models.Q(recipient_id=client_id))
        ).delete()
        return redirect(request.path)
    # Liste des clients ayant échangé avec le coach
    clients_ids = Message.objects.filter(recipient=request.user).values_list('sender', flat=True).distinct()
    clients = User.objects.filter(id__in=clients_ids)
    selected_id = request.GET.get('client')
    selected_client = None
    messages_list = []
    if selected_id:
        selected_client = User.objects.get(pk=selected_id)
        messages_list = Message.objects.filter(
            (models.Q(sender=request.user) & models.Q(recipient=selected_client)) |
            (models.Q(sender=selected_client) & models.Q(recipient=request.user))
        ).order_by('created_at')
        # Marquer les messages du client comme lus
        mark_messages_as_read(request.user, selected_client)
        if request.method == 'POST' and 'delete_contact_id' not in request.POST and 'delete_discussion_id' not in request.POST:
            from .forms import MessageForm
            form = MessageForm(request.POST, request.FILES)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.sender = request.user
                msg.recipient = selected_client
                msg.save()
                return redirect(f'{request.path}?client={selected_id}')
    else:
        form = None
    if selected_id and request.method != 'POST':
        from .forms import MessageForm
        form = MessageForm()
    # Ajout des messages de contact externe
    contact_messages = ContactMessage.objects.all().order_by('-date')
    is_coach = True
    context = {
        'clients': clients,
        'selected_client': selected_client,
        'messages_list': messages_list,
        'form': form,
        'selected_id': selected_id,
        'is_coach': is_coach,
        'contact_messages': contact_messages,
    }
    context = add_notifications_to_context(context, request.user)
    return render(request, 'rdv_app/messages_coach.html', context)

@login_required
def profil_client_view(request, user_id):
    from django.contrib.auth.models import User
    user_obj = get_object_or_404(User, pk=user_id)
    from .models import Profile
    profile, created = Profile.objects.get_or_create(user=user_obj)
    is_coach = True
    return render(request, 'rdv_app/profile.html', {
        'profile': profile,
        'user_obj': user_obj,
        'show_update_btn': False,
        'is_coach': is_coach,
    })

@login_required
def rdvs_client_view(request, user_id):
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from django.contrib.auth.models import User
    from .models import Seance
    client = User.objects.get(pk=user_id)
    seances = Seance.objects.filter(client=client).order_by('-date', '-heure_debut')
    is_coach = True
    return render(request, 'rdv_app/rdvs_client.html', {
        'client': client,
        'seances': seances,
        'is_coach': is_coach,
    })

def about_view(request):
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/about.html', {'is_coach': is_coach})

def services_view(request):
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/services.html', {'is_coach': is_coach})

def pricing_view(request):
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/pricing.html', {'is_coach': is_coach})

def contact_view(request):
    from django.core.mail import send_mail
    from .models import ContactMessage
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    success = False
    error = None
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if nom and email and message:
            try:
                # Enregistrement en base
                ContactMessage.objects.create(nom=nom, email=email, message=message, lu=False, type='contact_externe')
                # (Optionnel) Envoi email
                # send_mail(
                #     subject=f"Nouveau message de contact de {nom}",
                #     message=f"Nom: {nom}\nEmail: {email}\n\nMessage:\n{message}",
                #     from_email=None,
                #     recipient_list=['contact@boostcarriere.com'],
                #     fail_silently=False,
                # )
                success = True
            except Exception as e:
                error = str(e)
        else:
            error = "Veuillez remplir tous les champs."
    return render(request, 'rdv_app/contact.html', {'is_coach': is_coach, 'success': success, 'error': error})

def ateliers_view(request):
    ateliers = Atelier.objects.filter(date__gte=date.today()).order_by('date')
    inscrits = []
    if request.method == 'POST':
        if not request.user.is_authenticated:
            from django.urls import reverse
            return redirect(reverse('login') + '?next=' + reverse('ateliers'))
        atelier_id = request.POST.get('atelier_id')
        atelier = Atelier.objects.get(pk=atelier_id)
        atelier.participants.add(request.user)
        return redirect('mes_ateliers')
    if request.user.is_authenticated:
        inscrits = list(request.user.ateliers_inscrits.values_list('id', flat=True))
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/ateliers.html', {'ateliers': ateliers, 'inscrits': inscrits, 'is_coach': is_coach})

@login_required
def mes_ateliers_view(request):
    # Ateliers auxquels l'utilisateur est inscrit
    ateliers_inscrits = request.user.ateliers_inscrits.all().order_by('date')
    
    # Autres ateliers disponibles (non inscrit et date future)
    from datetime import date
    ateliers_disponibles = Atelier.objects.filter(
        date__gte=date.today()
    ).exclude(
        participants=request.user
    ).order_by('date')
    
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/mes_ateliers.html', {
        'ateliers_inscrits': ateliers_inscrits, 
        'ateliers_disponibles': ateliers_disponibles, 
        'is_coach': is_coach
    })

@staff_member_required
def ateliers_admin_view(request):
    ateliers = Atelier.objects.all().order_by('-date')
    form = AtelierForm()
    edit_id = request.GET.get('edit')
    inscrits_id = request.GET.get('inscrits')
    edit_atelier = None
    inscrits_atelier = None
    if edit_id:
        edit_atelier = Atelier.objects.get(pk=edit_id)
        form = AtelierForm(instance=edit_atelier)
    if inscrits_id:
        try:
            inscrits_atelier = Atelier.objects.get(pk=inscrits_id)
        except Atelier.DoesNotExist:
            inscrits_atelier = None
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            Atelier.objects.filter(pk=request.POST['delete_id']).delete()
            return redirect('ateliers_admin')
        post_edit_id = request.POST.get('edit_id')
        if post_edit_id:
            edit_atelier = Atelier.objects.get(pk=post_edit_id)
            form = AtelierForm(request.POST, request.FILES, instance=edit_atelier)
            if form.is_valid():
                form.save()
                return redirect('ateliers_admin')
        else:
            form = AtelierForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('ateliers_admin')
    is_coach = True
    return render(request, 'rdv_app/ateliers_admin.html', {
        'ateliers': ateliers,
        'form': form,
        'edit_id': edit_id,
        'edit_atelier': edit_atelier,
        'inscrits_atelier': inscrits_atelier,
        'is_coach': is_coach,
    })

@login_required
def disponibilites_coach_view(request):
    from .models import Indisponibilite
    from .forms import IndisponibiliteForm
    indispos = Indisponibilite.objects.filter(coach=request.user).order_by('-date_debut')
    indispo_form = IndisponibiliteForm(request.POST or None)
    if request.method == 'POST' and 'add_indispo' in request.POST:
        if indispo_form.is_valid():
            indispo = indispo_form.save(commit=False)
            indispo.coach = request.user
            indispo.save()
            return redirect('disponibilites_coach')
    if request.method == 'POST' and 'delete_indispo' in request.POST:
        ind_id = request.POST.get('delete_indispo')
        Indisponibilite.objects.filter(pk=ind_id, coach=request.user).delete()
        return redirect('disponibilites_coach')
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from .models import Disponibilite
    from .forms import DisponibiliteForm
    disponibilites = Disponibilite.objects.filter(coach=request.user).order_by('date', 'heure_debut')
    if request.method == 'POST':
        form = DisponibiliteForm(request.POST)
        if form.is_valid():
            dispo = form.save(commit=False)
            dispo.coach = request.user
            dispo.save()
            return redirect('disponibilites_coach')
    else:
        form = DisponibiliteForm()
    # Suppression
    delete_id = request.GET.get('delete')
    if delete_id:
        Disponibilite.objects.filter(pk=delete_id, coach=request.user).delete()
        return redirect('disponibilites_coach')
    from .models import Seance
    seances = Seance.objects.filter(date__gte=timezone.now().date()).order_by('date', 'heure_debut')
    is_coach = True
    return render(request, 'rdv_app/disponibilites_coach.html', {
        'disponibilites': disponibilites,
        'form': form,
        'indispo_form': indispo_form,
        'indispos': indispos,
        'seances': seances,
        'is_coach': True,
    })

@login_required
def clients_coach_view(request):
    """Vue pour afficher la liste des clients du coach"""
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import Seance, Profile
    
    # Récupérer tous les clients qui ont pris au moins un rendez-vous
    clients_ids = Seance.objects.values_list('client', flat=True).distinct()
    clients = User.objects.filter(id__in=clients_ids).order_by('first_name', 'last_name', 'username')
    
    # Statistiques pour chaque client
    clients_data = []
    total_rdv = 0
    clients_actifs = 0
    
    for client in clients:
        # Nombre de rendez-vous
        nb_rdv = Seance.objects.filter(client=client).count()
        total_rdv += nb_rdv
        
        # Dernier rendez-vous
        dernier_rdv = Seance.objects.filter(client=client).order_by('-date', '-heure_debut').first()
        # Prochain rendez-vous
        prochain_rdv = Seance.objects.filter(client=client, date__gte=timezone.now().date()).order_by('date', 'heure_debut').first()
        
        # Compter les clients actifs
        if prochain_rdv:
            clients_actifs += 1
        
        # Profil du client
        profile, created = Profile.objects.get_or_create(user=client)
        
        clients_data.append({
            'client': client,
            'profile': profile,
            'nb_rdv': nb_rdv,
            'dernier_rdv': dernier_rdv,
            'prochain_rdv': prochain_rdv,
        })
    
    is_coach = True
    return render(request, 'rdv_app/clients_coach.html', {
        'clients_data': clients_data,
        'total_clients': len(clients_data),
        'clients_actifs': clients_actifs,
        'total_rdv': total_rdv,
        'is_coach': is_coach,
    })

@login_required
def calendrier_coach_view(request):
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from .models import Seance, Atelier
    from datetime import datetime, date, timedelta
    import calendar
    from django.contrib.auth.models import User

    # Récupérer le mois et l'année à afficher
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Premier et dernier jour du mois
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    # Générer la grille du calendrier (semaines)
    cal = calendar.Calendar(firstweekday=0)  # Lundi=0
    month_days = list(cal.itermonthdates(year, month))
    weeks = [month_days[i:i+7] for i in range(0, len(month_days), 7)]

    # Récupérer les réservations (rendez-vous et ateliers) du mois
    # On considère que tous les Seance concernent le coach connecté
    seances = Seance.objects.filter(date__gte=first_day, date__lte=last_day)
    ateliers = Atelier.objects.filter(date__gte=first_day, date__lte=last_day)

    # Indexer les réservations par date
    reservations = {}
    for seance in seances:
        reservations.setdefault(seance.date, []).append({
            'type': 'rdv',
            'heure': seance.heure_debut,
            'client': seance.client.get_full_name() or seance.client.username,
            'objet': seance.objet,
            'id': seance.id,  # Ajout de l'identifiant du rendez-vous
        })
    for atelier in ateliers:
        reservations.setdefault(atelier.date, []).append({
            'type': 'atelier',
            'titre': atelier.titre,
            'participants': atelier.participants.count(),
        })

    # Pour navigation mois précédent/suivant
    prev_month = (month - 1) if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = (month + 1) if month < 12 else 1
    next_year = year if month < 12 else year + 1

    is_coach = True
    return render(request, 'rdv_app/calendrier_coach.html', {
        'weeks': weeks,
        'month': month,
        'year': year,
        'reservations': reservations,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'is_coach': is_coach,
    })

@login_required
def temoignage_client_view(request):
    if not request.user.groups.filter(name='client').exists():
        return redirect('accueil')
    # On cherche un témoignage existant pour ce client
    temoignage = Temoinage.objects.filter(user=request.user).first()
    deja_poste = temoignage is not None
    success = False
    # Si le témoignage existe et n'est pas validé, permettre l'édition
    if temoignage and not temoignage.valide:
        if request.method == 'POST':
            form = TemoinageForm(request.POST, instance=temoignage)
            if form.is_valid():
                form.save()
                success = True
        else:
            form = TemoinageForm(instance=temoignage)
        return render(request, 'rdv_app/temoignage_client.html', {'form': form, 'success': success, 'deja_poste': deja_poste, 'modifiable': True, 'temoignage': temoignage})
    # Si le témoignage existe et est validé, affichage simple, pas d'édition
    elif temoignage and temoignage.valide:
        return render(request, 'rdv_app/temoignage_client.html', {'success': False, 'deja_poste': True, 'modifiable': False, 'temoignage': temoignage})
    # Si pas encore de témoignage, création
    else:
        if request.method == 'POST':
            form = TemoinageForm(request.POST)
            if form.is_valid():
                temoignage = form.save(commit=False)
                temoignage.user = request.user
                temoignage.valide = False  # Validation admin requise
                temoignage.save()
                success = True
        else:
            form = TemoinageForm()
        return render(request, 'rdv_app/temoignage_client.html', {'form': form, 'success': success, 'deja_poste': False, 'modifiable': True, 'temoignage': None})

@login_required
def temoignages_admin_view(request):
    # Seuls les coachs peuvent accéder à la validation
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from .models import Temoinage
    if request.method == 'POST' and 'valider_id' in request.POST:
        temoignage_id = request.POST.get('valider_id')
        Temoinage.objects.filter(id=temoignage_id).update(valide=True)
        return redirect(request.path)
    if request.method == 'POST' and 'supprimer_id' in request.POST:
        temoignage_id = request.POST.get('supprimer_id')
        Temoinage.objects.filter(id=temoignage_id).delete()
        return redirect(request.path)
    temoignages = Temoinage.objects.all().order_by('-date')
    return render(request, 'rdv_app/temoignages_admin.html', {'temoignages': temoignages, 'is_coach': True})
