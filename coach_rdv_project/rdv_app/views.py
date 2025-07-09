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

def accueil(request):
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    if request.user.is_authenticated:
        return render(request, 'rdv_app/accueil_public.html', {'is_coach': is_coach})
    return render(request, 'rdv_app/accueil.html', {'is_coach': is_coach})

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

@login_required
def prendre_rdv(request):
    from .models import Disponibilite, Seance
    # On récupère les créneaux disponibles (non réservés)
    # Un créneau est réservé s'il existe une Seance à la même date, heure_debut, heure_fin
    creneaux_reserves = Seance.objects.values_list('date', 'heure_debut', 'heure_fin')
    disponibilites = Disponibilite.objects.exclude(
        models.Q(date__in=[c[0] for c in creneaux_reserves],
                 heure_debut__in=[c[1] for c in creneaux_reserves],
                 heure_fin__in=[c[2] for c in creneaux_reserves])
    ).filter(restreint=False).order_by('date', 'heure_debut')
    if request.method == 'POST':
        dispo_id = request.POST.get('disponibilite')
        if dispo_id:
            dispo = Disponibilite.objects.get(pk=dispo_id)
            seance = Seance.objects.create(
                client=request.user,
                date=dispo.date,
                heure_debut=dispo.heure_debut,
                heure_fin=dispo.heure_fin
            )
            return redirect('dashboard')
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/prise_rdv.html', {'disponibilites': disponibilites, 'is_coach': is_coach})

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
    from .models import Disponibilite, Seance
    seance = get_object_or_404(Seance, pk=pk, client=request.user)
    # Créneaux déjà réservés par d'autres
    creneaux_reserves = Seance.objects.exclude(pk=seance.pk).values_list('date', 'heure_debut')
    disponibilites = Disponibilite.objects.exclude(
        models.Q(date__in=[c[0] for c in creneaux_reserves],
                 heure_debut__in=[c[1] for c in creneaux_reserves])
    ).order_by('date', 'heure_debut')
    # On ajoute le créneau actuel du rendez-vous à la liste
    if not disponibilites.filter(date=seance.date, heure_debut=seance.heure_debut).exists():
        from django.utils.safestring import mark_safe
        seance_dispo = Disponibilite(
            id=0,  # id fictif pour le template
            coach=request.user,
            date=seance.date,
            heure_debut=seance.heure_debut,
            heure_fin=None
        )
        disponibilites = list(disponibilites) + [seance_dispo]
    if request.method == 'POST':
        dispo_id = request.POST.get('disponibilite')
        if dispo_id and dispo_id != '0':
            dispo = Disponibilite.objects.get(pk=dispo_id)
            seance.date = dispo.date
            seance.heure_debut = dispo.heure_debut
            seance.save()
            messages.success(request, 'Votre rendez-vous a bien été modifié.')
            return redirect('dashboard')
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/seance_update.html', {'seance': seance, 'disponibilites': disponibilites, 'is_coach': is_coach})

@login_required
def seance_delete_view(request, pk):
    seance = get_object_or_404(Seance, pk=pk)
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    # Seul le client ou le coach peut annuler
    if not (request.user == seance.client or is_coach):
        return redirect('dashboard')
    if request.method == 'POST':
        client = seance.client
        coach = seance.client if not is_coach else request.user
        # Message interne
        from .models import Message
        Message.objects.create(
            sender=coach,
            recipient=client,
            content=f"Votre rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')} a été annulé par le coach."
        )
        # Email
        from django.core.mail import send_mail
        send_mail(
            subject="Annulation de votre rendez-vous CoachRDV",
            message=f"Bonjour {client.first_name},\n\nVotre rendez-vous du {seance.date} à {seance.heure_debut.strftime('%H:%M')} a été annulé par le coach. N'hésitez pas à reprendre rendez-vous sur la plateforme.\n\nCordialement,\nCoachRDV",
            from_email=None,
            recipient_list=[client.email],
            fail_silently=True,
        )
        seance.delete()
        messages.success(request, 'Le rendez-vous a bien été annulé et le client a été notifié.')
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
    return render(request, 'rdv_app/messages.html', {
        'form': form,
        'messages_list': messages_list,
        'coach': coach,
        'discussions': discussions,
        'selected_id': int(selected_id) if selected_id else coach.id,
        'show_new': show_new,
        'is_coach': is_coach,
    })

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
    return render(request, 'rdv_app/messages_coach.html', {
        'clients': clients,
        'selected_client': selected_client,
        'messages_list': messages_list,
        'form': form,
        'selected_id': selected_id,
        'is_coach': is_coach,
    })

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
    ateliers = request.user.ateliers_inscrits.all().order_by('date')
    is_coach = request.user.is_authenticated and (request.user.groups.filter(name='coach').exists() or request.user.username.lower() == 'adja')
    return render(request, 'rdv_app/mes_ateliers.html', {'ateliers': ateliers, 'is_coach': is_coach})

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
