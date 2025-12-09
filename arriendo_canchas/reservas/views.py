from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from .models import Reserva, Cancha, FechasNoDisponibles, Categoria
import calendar
import json



FERIADOS_BASE = [
    ("01-01"),
    ("04-18"),
    ("04-19"), 
    ("05-01"),
    ("05-21"),
    ("06-29"),
    ("07-16"),
    ("08-15"),
    ("09-18"),
    ("09-19"),
    ("10-12"),
    ("11-01"),
    ("12-08"),
    ("12-25"),
]

def generar_feriados():
    hoy = date.today()
    año_actual = hoy.year
    año_siguiente = hoy.year + 1
    feriados = []
    for base in FERIADOS_BASE:
        feriados.append(f"{año_actual}-{base}")
        feriados.append(f"{año_siguiente}-{base}")
    return feriados

FERIADOS_PREDETERMINADOS = generar_feriados()




def home(request):
    categoria_filtro = request.GET.get("categoria")
    categorias = Categoria.objects.all()

    if categoria_filtro:
        canchas = Cancha.objects.filter(categoria__id=categoria_filtro)
    else:
        canchas = Cancha.objects.all()

    for c in canchas:
        bloqueo = FechasNoDisponibles.objects.filter(
            cancha=c,
            fecha_fin__gte=date.today()
        ).order_by("fecha_inicio").first()
        c.bloqueo = bloqueo

    return render(request, "home.html", {
        "canchas": canchas,
        "categorias": categorias,
        "categoria_filtro": categoria_filtro,
    })


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


def api_horas_ocupadas(request):
    fecha = request.GET.get("fecha")
    cancha_id = request.GET.get("cancha")

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()

    reservas = Reserva.objects.filter(
        cancha_id=cancha_id,
        fecha=fecha_obj,
        estado__in=["Pendiente", "Pagado"]
    )

    horas_ocupadas = []

    for r in reservas:
        actual = datetime.combine(date.today(), r.hora_inicio)
        fin = datetime.combine(date.today(), r.hora_fin)
        while actual < fin:
            horas_ocupadas.append(actual.strftime("%H:%M"))
            actual += timedelta(minutes=30)

    return JsonResponse({"ocupadas": horas_ocupadas})


@login_required
def reservar(request, cancha_id):
    cancha = get_object_or_404(Cancha, id=cancha_id)

    horas_manana = ["09:00","09:30","10:00","10:30","11:00","11:30"]
    horas_tarde = ["12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30"]
    horas_noche = ["18:00","18:30","19:00","19:30","20:00","20:30"]

    todas_las_horas = horas_manana + horas_tarde + horas_noche
    horas_json = json.dumps(todas_las_horas)


    bloqueos_qs = FechasNoDisponibles.objects.filter(cancha=cancha)
    bloqueos_list = []

    for b in bloqueos_qs:
        current = b.fecha_inicio
        while current <= b.fecha_fin:
            bloqueos_list.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

    bloqueos_list.extend(FERIADOS_PREDETERMINADOS)

    bloqueos_json = json.dumps(bloqueos_list)


    if request.method == "POST":
        fecha_str = request.POST.get("fecha")
        rango_horas = request.POST.get("hora")

        if not fecha_str or not rango_horas:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "horas_json": horas_json,
                "horas_manana": horas_manana,
                "horas_tarde": horas_tarde,
                "horas_noche": horas_noche,
                "bloqueos_json": bloqueos_json,
            })

        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        try:
            hora_inicio_str, hora_fin_str = rango_horas.split("-")
        except ValueError:
            hora_inicio_str = hora_fin_str = rango_horas

        hora_inicio_obj = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_fin_obj = datetime.strptime(hora_fin_str, "%H:%M").time()

        if fecha_str in bloqueos_list:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "horas_json": horas_json,
                "horas_manana": horas_manana,
                "horas_tarde": horas_tarde,
                "horas_noche": horas_noche,
                "bloqueos_json": bloqueos_json,
                "error": "La cancha está bloqueada este día."
            })

        conflicto = Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha_obj,
            hora_inicio__lt=hora_fin_obj,
            hora_fin__gt=hora_inicio_obj,
            estado__in=["Pendiente", "Pagado"]
        ).exists()

        if conflicto:
            return render(request, "reservar.html", {
                "cancha": cancha,
                "horas_json": horas_json,
                "horas_manana": horas_manana,
                "horas_tarde": horas_tarde,
                "horas_noche": horas_noche,
                "bloqueos_json": bloqueos_json,
                "error": "Este rango de horas ya está reservado."
            })

        Reserva.objects.create(
            cancha=cancha,
            usuario=request.user,
            fecha=fecha_obj,
            hora_inicio=hora_inicio_obj,
            hora_fin=hora_fin_obj,
            estado="Pendiente"
        )

        return redirect("mis_reservas")

    return render(request, "reservar.html", {
        "cancha": cancha,
        "horas_json": horas_json,
        "horas_manana": horas_manana,
        "horas_tarde": horas_tarde,
        "horas_noche": horas_noche,
        "bloqueos_json": bloqueos_json,
    })


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).order_by("-fecha", "-hora_inicio")
    return render(request, "mis_reservas.html", {"reservas": reservas})


@login_required
def cancelar(request, id):
    reserva = get_object_or_404(Reserva, id=id, usuario=request.user)
    reserva.estado = "Cancelado"
    reserva.save()
    return redirect("mis_reservas")


@login_required
def pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    return render(request, "pago.html", {"reserva": reserva})


@login_required
def pago_exitoso(request):
    return render(request, "pago_exitoso.html")


@login_required
def calendario(request):
    hoy = date.today()
    year = int(request.GET.get("year", hoy.year))
    month = int(request.GET.get("month", hoy.month))

    cal = calendar.Calendar()
    dias = []

    for d in cal.itermonthdates(year, month):

        es_bloqueado = (
            FechasNoDisponibles.objects.filter(
                fecha_inicio__lte=d,
                fecha_fin__gte=d
            ).exists()
            or d.strftime("%Y-%m-%d") in FERIADOS_PREDETERMINADOS
        )

        dias.append({
            "date": d,
            "in_month": d.month == month,
            "bloqueado": es_bloqueado
        })

    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    return render(request, "calendario.html", {
        "year": year,
        "month": month,
        "dias": dias,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })
