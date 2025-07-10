from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.accueil, name='accueil'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='rdv_app/login.html'), name='login'),
     path('logout/', LogoutView.as_view(next_page='accueil'), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('choix-auth/', views.choix_auth_view, name='choix_auth'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('coach/dashboard/', views.dashboard_coach_view, name='dashboard_coach'),

    # Prise de RDV
    path('prendre-rdv/', views.prendre_rdv, name='prise_rdv'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update_view, name='profile_update'),

    path('about/', views.about_view, name='about'),

    path('services/', views.services_view, name='services'),

    path('tarifs/', views.pricing_view, name='pricing'),

    path('contact/', views.contact_view, name='contact'),

    path('rendezvous/<int:pk>/modifier/', views.seance_update_view, name='seance_update'),
    path('rendezvous/<int:pk>/annuler/', views.seance_delete_view, name='seance_delete'),
    path('messages/', views.messages_view, name='messages'),
    path('messages_coach/', views.messages_coach_view, name='messages_coach'),
    path('ateliers/', views.ateliers_view, name='ateliers'),
    path('coach/ateliers/', views.ateliers_admin_view, name='ateliers_admin'),
    path('mes-ateliers/', views.mes_ateliers_view, name='mes_ateliers'),
    path('disponibilites_coach/', views.disponibilites_coach_view, name='disponibilites_coach'),
    path('clients_coach/', views.clients_coach_view, name='clients_coach'),
    path('profil_client/<int:user_id>/', views.profil_client_view, name='profil_client'),
    path('client/<int:user_id>/rdvs/', views.rdvs_client_view, name='rdvs_client'),
    path('coach/calendrier/', views.calendrier_coach_view, name='calendrier_coach'),
]
