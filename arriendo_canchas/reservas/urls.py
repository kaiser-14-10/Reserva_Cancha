from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("reservar/<int:cancha_id>/", views.reservar, name="reservar"),
    path("mis-reservas/", views.mis_reservas, name="mis_reservas"),
    path("cancelar/<int:id>/", views.cancelar, name="cancelar"),
    path("calendario/", views.calendario, name="calendario"),


    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("register/", views.register, name="register"),
    path('pago/<int:reserva_id>/', views.pago, name='pago'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path("api/horas_ocupadas/", views.api_horas_ocupadas, name="api_horas_ocupadas"),



]

