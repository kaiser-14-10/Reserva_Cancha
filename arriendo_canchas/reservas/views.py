from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from .models import Reserva, Cancha, FechasNoDisponibles
import calendar
import json

FECHA_LIMITE = date.today() + timedelta(days=30)


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


def home(request):
    canchas = Cancha.objects.all()
    hoy = date.today()

    bloqueos = FechasNoDisponibles.objects.filter(
        fecha_fin__gte=hoy
    ).order_by("fecha_fin")

    return render(request, "home.html", {
        "canchas": canchas,
        "bloqueos": bloqueos
    })


@login_required
def reservar(request, cancha_id):
    cancha = get_object_or_404(Cancha, id=cancha_id)
    hoy = date.today()

    horas = []
    for h in range(9, 21):
        horas.append(f"{h:02d}:00")
        horas.append(f"{h:02d}:30")

    dias_mes = []
    for i in range(1, 32):
        try:
            d = date(hoy.year, hoy.month, i)
        except ValueError:
            continue

        bloqueado_admin = FechasNoDisponibles.objects.filter(
            cancha=cancha,
            fecha_inicio__lte=d,
            fecha_fin__gte=d
        ).exists()

        dias_mes.append({
            "fecha": d,
            "bloqueado": bloqueado_admin,
            "pasado": d < hoy,
            "fuera_limite": d > FECHA_LIMITE,
        })

    if request.method == "POST":
        dia = request.POST.get("fecha")
        hora = request.POST.get("hora")

        try:
            fecha_obj = datetime.strptime(dia, "%Y-%m-%d").date()
        except:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas_json": json.dumps(horas),
                "error": "Formato de fecha inválido."
            })

        if fecha_obj > FECHA_LIMITE:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas_json": json.dumps(horas),
                "error": "No puedes reservar después de la fecha límite."
            })

        try:
            hora_obj = datetime.strptime(hora, "%H:%M").time()
        except:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas_json": json.dumps(horas),
                "error": "Formato de hora inválido."
            })

        conflicto = Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha_obj,
            hora=hora_obj,
            estado__in=["Pendiente", "Pagado"]
        ).exists()

        if conflicto:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas_json": json.dumps(horas),
                "error": "Ya existe una reserva en ese día/hora."
            })

        Reserva.objects.create(
            usuario=request.user,
            cancha=cancha,
            fecha=fecha_obj,
            hora=hora_obj,
            estado="Pendiente"
        )

        return redirect("mis_reservas")

    return render(request, "reservar.html", {
        "cancha": cancha,
        "dias_mes": dias_mes,
        "horas_json": json.dumps(horas),
    })



@login_required
def api_horas_ocupadas(request):
    fecha = request.GET.get("fecha")
    cancha_id = request.GET.get("cancha")

    ocupadas = Reserva.objects.filter(
        fecha=fecha,
        cancha_id=cancha_id,
        estado__in=["Pendiente", "Pagado"]
    ).values_list("hora", flat=True)

    ocupadas_string = [t.strftime("%H:%M") for t in ocupadas]

    return JsonResponse({"ocupadas": ocupadas_string})



@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(
        usuario=request.user
    ).order_by("fecha")

    return render(request, "mis_reservas.html", {"reservas": reservas})



@login_required
def cancelar(request, id):
    r = get_object_or_404(Reserva, id=id, usuario=request.user)
    r.estado = "Cancelado"
    r.save()
    return redirect("mis_reservas")



def calendario(request):
    return render(request, "calendario.html")


@login_required
def pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if request.method == "POST":
        reserva.estado = "Pagado"
        reserva.save()
        return redirect("pago_exitoso")

    return render(request, "pago.html", {"reserva": reserva})



@login_required
def pago_exitoso(request):
    return render(request, "pago_exitoso.html")
