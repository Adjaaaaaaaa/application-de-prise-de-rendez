from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Seance, Profile, Message
from .forms import SeanceForm, SignupForm, ProfileForm, ProfileFullForm, MessageForm
from datetime import date
from django.contrib import messages
from django.db import models

def accueil(request):
    if request.user.is_authenticated:
        return render(request, 'rdv_app/accueil_public.html')
    return render(request, 'rdv_app/accueil.html')

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
    return render(request, 'rdv_app/signup.html', {'form': form})

@login_required
def dashboard(request):
    is_coach = request.user.groups.filter(name='coach').exists() or request.user.is_superuser
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
    return render(request, template, context)

@login_required
def prendre_rdv(request):
    if request.method == 'POST':
        form = SeanceForm(request.POST)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.client = request.user
            seance.save()
            return redirect('dashboard')
    else:
        form = SeanceForm()
    return render(request, 'rdv_app/prise_rdv.html', {'form': form})

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'rdv_app/profile.html', {
        'profile': profile,
        'user_obj': request.user,
        'show_update_btn': True
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
    return render(request, 'rdv_app/profile_update.html', {'form': form, 'profile': profile, 'user_obj': request.user})

@login_required
def seance_update_view(request, pk):
    seance = get_object_or_404(Seance, pk=pk, client=request.user)
    if request.method == 'POST':
        form = SeanceForm(request.POST, instance=seance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre rendez-vous a bien été modifié.')
            return redirect('dashboard')
    else:
        form = SeanceForm(instance=seance)
    return render(request, 'rdv_app/seance_update.html', {'form': form, 'seance': seance})

@login_required
def seance_delete_view(request, pk):
    seance = get_object_or_404(Seance, pk=pk, client=request.user)
    if request.method == 'POST':
        seance.delete()
        messages.success(request, 'Votre rendez-vous a bien été annulé.')
        return redirect('dashboard')
    return render(request, 'rdv_app/seance_confirm_delete.html', {'seance': seance})

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
    return render(request, 'rdv_app/messages.html', {
        'form': form,
        'messages_list': messages_list,
        'coach': coach,
        'discussions': discussions,
        'selected_id': int(selected_id) if selected_id else coach.id,
        'show_new': show_new,
    })

def about_view(request):
    return render(request, 'rdv_app/about.html')

def services_view(request):
    return render(request, 'rdv_app/services.html')

def pricing_view(request):
    return render(request, 'rdv_app/pricing.html')

def contact_view(request):
    return render(request, 'rdv_app/contact.html')
