from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Seance, Profile, Message, Atelier
from .forms import SeanceForm, SignupForm, ProfileForm, ProfileFullForm, MessageForm
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
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    context = {'is_coach': is_coach}
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
            return redirect('dashboard')
    else:
        form = SignupForm()
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/signup.html', {'form': form, 'is_coach': is_coach})

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
    from .models import Seance
    # Affiche tous les rendez-vous à venir pour le coach (où il est coach)
    seances = Seance.objects.filter(date__gte=timezone.now().date()).order_by('date', 'heure_debut')
    # Vérification du rôle coach
    if not (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja'):
        return redirect('dashboard')
    from .models import Atelier, Seance, Message
    nb_ateliers = Atelier.objects.count()
    nb_clients = Seance.objects.values('client').distinct().count()
    nb_messages = Message.objects.filter(recipient=request.user).count()
    ateliers = Atelier.objects.order_by('-date')[:3]
    is_coach = True
    return render(request, 'rdv_app/dashboard_coach.html', {
        'nb_ateliers': nb_ateliers,
        'nb_clients': nb_clients,
        'nb_messages': nb_messages,
        'ateliers': ateliers,
        'is_coach': is_coach,
        'seances': seances,
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
    from .models import Seance, Message
    from django.core.mail import send_mail
    seance = get_object_or_404(Seance, pk=pk)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    # Seul le client ou le coach peut modifier
    if not (request.user == seance.client or is_coach):
        return redirect('dashboard')
    if request.method == 'POST':
        from datetime import datetime
        # Récupération des nouvelles valeurs
        new_date = request.POST.get('date')
        new_heure = request.POST.get('heure_debut')
        new_objet = request.POST.get('objet')
        # Vérification que le nouveau créneau n'est pas déjà pris
        from .models import Seance
        conflit = Seance.objects.filter(
            date=new_date, 
            heure_debut=new_heure
        ).exclude(pk=seance.pk).exists()
        if conflit:
            messages.error(request, 'Ce créneau est déjà réservé.')
        else:
            # Sauvegarde des anciennes valeurs pour la notification
            old_date = seance.date
            old_heure = seance.heure_debut
            # Mise à jour du rendez-vous
            seance.date = new_date
            seance.heure_debut = new_heure
            seance.objet = new_objet
            seance.save()
            # Notification au client si c'est le coach qui modifie
            if is_coach:
                client = seance.client
                # Message interne
                Message.objects.create(
                    sender=request.user,
                    recipient=client,
                    content=f"Votre rendez-vous a été modifié : {old_date} {old_heure.strftime('%H:%M')} → {new_date} {new_heure}. Nouvel objet : {new_objet}"
                )
                # Email
                send_mail(
                    subject="Modification de votre rendez-vous Boost Carrière",
                    message=f"Bonjour {client.first_name},\n\nVotre rendez-vous a été modifié par le coach :\n- Ancien : {old_date} à {old_heure.strftime('%H:%M')}\n- Nouveau : {new_date} à {new_heure}\n- Objet : {new_objet}\n\nCordialement,\nBoost Carrière",
                    from_email=None,
                    recipient_list=[client.email],
                    fail_silently=True,
                )
            else:
                # Client modifie → notifier le coach
                from django.contrib.auth.models import User
                coach = User.objects.filter(username='adja').first() or User.objects.filter(is_staff=True).first()
                # Message interne
                Message.objects.create(
                    sender=request.user,
                    recipient=coach,
                    content=f"Le client {seance.client.get_full_name()} a modifié son rendez-vous : {old_date} {old_heure.strftime('%H:%M')} → {new_date} {new_heure}. Nouvel objet : {new_objet}"
                )
                # Email
                send_mail(
                    subject="Modification de rendez-vous par le client",
                    message=f"Bonjour,\n\nLe client {seance.client.get_full_name()} ({seance.client.email}) a modifié son rendez-vous :\n- Ancien : {old_date} à {old_heure.strftime('%H:%M')}\n- Nouveau : {new_date} à {new_heure}\n- Objet : {new_objet}\n\nCordialement,\nBoost Carrière",
                    from_email=None,
                    recipient_list=[coach.email],
                    fail_silently=True,
                )
            messages.success(request, 'Le rendez-vous a bien été modifié.')
            return redirect('dashboard')
    return render(request, 'rdv_app/seance_update.html', {'seance': seance, 'is_coach': is_coach})

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
        return redirect('dashboard')
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
    from .models import Message
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
        if request.method == 'POST':
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
    is_coach = True
    context = {
        'clients': clients,
        'selected_client': selected_client,
        'messages_list': messages_list,
        'form': form,
        'selected_id': selected_id,
        'is_coach': is_coach,
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
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/contact.html', {'is_coach': is_coach})

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
    edit_atelier = None
    if edit_id:
        edit_atelier = Atelier.objects.get(pk=edit_id)
        form = AtelierForm(instance=edit_atelier)
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            Atelier.objects.filter(pk=request.POST['delete_id']).delete()
            return redirect('ateliers_admin')
        elif edit_id:
            form = AtelierForm(request.POST, instance=edit_atelier)
            if form.is_valid():
                form.save()
                return redirect('ateliers_admin')
        else:
            form = AtelierForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('ateliers_admin')
    is_coach = True
    return render(request, 'rdv_app/ateliers_admin.html', {
        'ateliers': ateliers,
        'form': form,
        'edit_id': edit_id,
        'edit_atelier': edit_atelier,
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
