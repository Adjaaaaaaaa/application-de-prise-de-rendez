from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Seance
from .forms import SeanceForm
from datetime import date

def accueil(request):
    return render(request, 'rdv_app/accueil.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Affecter au groupe "client" automatiquement
            group, created = Group.objects.get_or_create(name='client')
            user.groups.add(group)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'rdv_app/signup.html', {'form': form})

@login_required
def dashboard(request):
    # Vérification plus claire du rôle
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
        seances = Seance.objects.filter(client=request.user).order_by('date', 'heure_debut')
        template = 'rdv_app/dashboard_client.html'
        context = {'seances': seances}
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

def about_view(request):
    return render(request, 'rdv_app/about.html')

def services_view(request):
    return render(request, 'rdv_app/services.html')

def pricing_view(request):
    return render(request, 'rdv_app/pricing.html')

def contact_view(request):
    return render(request, 'rdv_app/contact.html')
