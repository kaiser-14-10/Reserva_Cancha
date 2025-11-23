from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('reservar/<int:cancha_id>/', views.reservar, name='reservar'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:id>/', views.cancelar_reserva, name='cancelar'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),

]
