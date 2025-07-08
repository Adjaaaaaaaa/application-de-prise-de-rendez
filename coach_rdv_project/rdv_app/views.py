from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Seance
from .forms import SeanceForm

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
        template = 'rdv_app/dashboard_coach.html'
    else:
        seances = Seance.objects.filter(client=request.user).order_by('date', 'heure_debut')
        template = 'rdv_app/dashboard_client.html'
    return render(request, template, {'seances': seances})

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
