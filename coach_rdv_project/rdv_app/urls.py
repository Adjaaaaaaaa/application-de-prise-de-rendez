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

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),

    # Prise de RDV
    path('prendre-rdv/', views.prendre_rdv, name='prise_rdv'),
]
