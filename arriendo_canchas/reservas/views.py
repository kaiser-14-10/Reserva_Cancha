from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cancha, Reserva, Log
from datetime import date

def home(request):
    canchas = Cancha.objects.all()
    return render(request, 'home.html', {'canchas': canchas})

@login_required
def reservar(request, cancha_id):
    cancha = Cancha.objects.get(id=cancha_id)
    if request.method == 'POST':
        fecha = request.POST['fecha']
        hora = request.POST['hora']
        Reserva.objects.create(cancha=cancha, usuario=request.user, fecha=fecha, hora=hora)
        Log.objects.create(usuario=request.user, accion=f"Reservó {cancha.nombre}")
        messages.success(request, 'Reserva realizada correctamente.')
        return redirect('home')
    return render(request, 'reservar.html', {'cancha': cancha})

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, 'mis_reservas.html', {'reservas': reservas})

@login_required
def cancelar_reserva(request, id):
    reserva = Reserva.objects.get(id=id, usuario=request.user)
    reserva.estado = 'Cancelado'
    reserva.save()
    Log.objects.create(usuario=request.user, accion=f"Canceló reserva {reserva.cancha.nombre}")
    messages.info(request, 'Reserva cancelada.')
    return redirect('mis_reservas')
