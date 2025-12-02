from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, timedelta
from .models import Reserva, Cancha, FechasNoDisponibles
import calendar


DIAS_BLOQUEADOS = []
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
                "horas": horas,
                "error": "Formato de fecha inválido."
            })

        if fecha_obj > FECHA_LIMITE:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas": horas,
                "error": "No puedes reservar después de la fecha límite."
            })

        bloqueo = FechasNoDisponibles.objects.filter(
            cancha=cancha,
            fecha_inicio__lte=fecha_obj,
            fecha_fin__gte=fecha_obj
        ).first()

        if bloqueo:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas": horas,
                "error": f"La cancha no está disponible hasta el {bloqueo.fecha_fin}"
            })

        try:
            hora_obj = datetime.strptime(hora, "%H:%M").time()
        except:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "dias_mes": dias_mes,
                "horas": horas,
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
                "horas": horas,
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
        "horas": horas
    })


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(
        usuario=request.user
    ).order_by("fecha")

    for r in reservas:
        bloqueo = FechasNoDisponibles.objects.filter(
            cancha=r.cancha,
            fecha_inicio__lte=r.fecha,
            fecha_fin__gte=r.fecha
        ).first()

        r.aviso = None
        if bloqueo:
            r.aviso = (
                f"La cancha no estará disponible hasta {bloqueo.fecha_fin} "
                f"{('('+bloqueo.motivo+')') if bloqueo.motivo else ''}"
            )

    return render(request, "mis_reservas.html", {"reservas": reservas})


@login_required
def cancelar(request, id):
    r = get_object_or_404(Reserva, id=id, usuario=request.user)
    r.estado = "Cancelado"
    r.save()
    return redirect("mis_reservas")


def calendario(request):
    hoy = date.today()
    year = int(request.GET.get("year", hoy.year))
    month = int(request.GET.get("month", hoy.month))

    cal = calendar.Calendar(firstweekday=0)
    dias_mes = list(cal.itermonthdates(year, month))

    bloqueos = FechasNoDisponibles.objects.all()
    dias_bloqueados = set()

    for b in bloqueos:
        delta = (b.fecha_fin - b.fecha_inicio).days + 1
        for i in range(delta):
            dias_bloqueados.add(b.fecha_inicio + timedelta(days=i))

    dias = []
    for d in dias_mes:
        dias.append({
            "date": d,
            "in_month": d.month == month,
            "bloqueado": d in dias_bloqueados
        })

    return render(request, "calendario.html", {
        "dias": dias,
        "year": year,
        "month": month
    })


@login_required
def pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if request.method == "POST":
        tarjeta = request.POST.get("tarjeta")
        cvv = request.POST.get("cvv")
        correo = request.POST.get("correo")

        reserva.estado = "Pagado"
        reserva.save()

        return redirect("pago_exitoso")

    return render(request, "pago.html", {"reserva": reserva})


@login_required
def pago_exitoso(request):
    return render(request, "pago_exitoso.html")
