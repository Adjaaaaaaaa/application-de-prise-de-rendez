from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.accueil, name='accueil'),

    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
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
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='rdv_app/password_change.html',
        success_url='/profile/'
    ), name='password_change'),

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
    path('temoignage/', views.temoignage_client_view, name='temoignage_client'),
    path('coach/temoignages/', views.temoignages_admin_view, name='temoignages_admin'),
]
