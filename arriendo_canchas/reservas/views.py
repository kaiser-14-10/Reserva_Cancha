from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from .models import (
    Reserva, Cancha, Categoria,
    HorasNoDisponibles, DiaBloqueado, FechasNoDisponibles
)
import calendar
import json



FERIADOS_BASE = [
    "01-01","04-18","04-19","05-01","05-21","06-29",
    "07-16","08-15","09-18","09-19","10-12","11-01",
    "12-08","12-25",
]

def generar_feriados():
    hoy = date.today()
    years = [hoy.year, hoy.year + 1]
    return [f"{y}-{d}" for y in years for d in FERIADOS_BASE]

FERIADOS_PREDETERMINADOS = generar_feriados()


def home(request):
    categoria_filtro = request.GET.get("categoria")
    categorias = Categoria.objects.all()

    canchas = (
        Cancha.objects.filter(categoria__id=categoria_filtro)
        if categoria_filtro else Cancha.objects.all()
    )

    return render(request, "home.html", {
        "canchas": canchas,
        "categorias": categorias,
        "categoria_filtro": categoria_filtro,
    })


def api_horas_ocupadas(request):
    fecha = request.GET.get("fecha")
    cancha_id = request.GET.get("cancha")

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except:
        return JsonResponse({"ocupadas": [], "bloqueadas": []})

    ocupadas = set()
    bloqueadas = set()

    if (
        DiaBloqueado.objects.filter(cancha_id=cancha_id, fecha=fecha_obj).exists()
        or FechasNoDisponibles.objects.filter(
            cancha_id=cancha_id,
            fecha_inicio__lte=fecha_obj,
            fecha_fin__gte=fecha_obj
        ).exists()
        or fecha in FERIADOS_PREDETERMINADOS
    ):
        actual = datetime.strptime("00:00", "%H:%M")
        fin = datetime.strptime("23:30", "%H:%M")
        while actual <= fin:
            bloqueadas.add(actual.strftime("%H:%M"))
            actual += timedelta(minutes=30)

        return JsonResponse({"ocupadas": [], "bloqueadas": sorted(bloqueadas)})

    for b in HorasNoDisponibles.objects.filter(cancha_id=cancha_id, fecha=fecha_obj):
        actual = datetime.combine(date.today(), b.hora_inicio)
        fin = datetime.combine(date.today(), b.hora_fin) + timedelta(minutes=30)

        while actual < fin:
            bloqueadas.add(actual.strftime("%H:%M"))
            actual += timedelta(minutes=30)

    for r in Reserva.objects.filter(
        cancha_id=cancha_id,
        fecha=fecha_obj,
        estado__in=["Pendiente", "Pagado"]
    ):
        actual = datetime.combine(date.today(), r.hora_inicio)
        fin = datetime.combine(date.today(), r.hora_fin) + timedelta(minutes=30)

        while actual < fin:
            ocupadas.add(actual.strftime("%H:%M"))
            actual += timedelta(minutes=30)

    return JsonResponse({
        "ocupadas": sorted(ocupadas),
        "bloqueadas": sorted(bloqueadas)
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


@login_required
def reservar(request, cancha_id):
    cancha = get_object_or_404(Cancha, id=cancha_id)

    horas = []
    actual = datetime.strptime("09:00", "%H:%M")
    fin = datetime.strptime("22:00", "%H:%M")
    while actual <= fin:
        horas.append(actual.strftime("%H:%M"))
        actual += timedelta(minutes=30)

    horas_json = json.dumps(horas)


    bloqueos_fecha = set()

    for d in DiaBloqueado.objects.filter(cancha=cancha):
        bloqueos_fecha.add(d.fecha.strftime("%Y-%m-%d"))

    for b in FechasNoDisponibles.objects.filter(cancha=cancha):
        d = b.fecha_inicio
        while d <= b.fecha_fin:
            bloqueos_fecha.add(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)

    bloqueos_fecha.update(FERIADOS_PREDETERMINADOS)


    bloqueos_horas = {}

    for b in HorasNoDisponibles.objects.filter(cancha=cancha):
        key = b.fecha.strftime("%Y-%m-%d")
        bloqueos_horas.setdefault(key, set())

        actual = datetime.combine(date.today(), b.hora_inicio)
        fin = datetime.combine(date.today(), b.hora_fin) + timedelta(minutes=30)

        while actual < fin:
            bloqueos_horas[key].add(actual.strftime("%H:%M"))
            actual += timedelta(minutes=30)

    bloqueos_horas_json = json.dumps({k: sorted(v) for k, v in bloqueos_horas.items()})


    if request.method == "POST":
        fecha_str = request.POST.get("fecha")
        hora_str = request.POST.get("hora")

        if not fecha_str or not hora_str:
            return redirect("reservar", cancha_id=cancha.id)

        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        h_ini, h_fin = hora_str.split("-")

        hora_inicio = datetime.strptime(h_ini, "%H:%M").time()
        hora_fin = datetime.strptime(h_fin, "%H:%M").time()

        Reserva.objects.create(
            cancha=cancha,
            usuario=request.user,
            fecha=fecha_obj,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado="Pendiente"
        )

        return redirect("mis_reservas")

    return render(request, "reservar.html", {
        "cancha": cancha,
        "horas_json": horas_json,
        "bloqueos_json": json.dumps(sorted(bloqueos_fecha)),
        "bloqueos_horas_json": bloqueos_horas_json
    })



@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).order_by("-fecha")
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
    if request.method == "POST":
        reserva.estado = "Pagado"
        reserva.save()
        return redirect("pago_exitoso")
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
        dias.append({
            "date": d,
            "in_month": d.month == month,
            "bloqueado": (
                DiaBloqueado.objects.filter(fecha=d).exists()
                or FechasNoDisponibles.objects.filter(
                    fecha_inicio__lte=d,
                    fecha_fin__gte=d
                ).exists()
                or d.strftime("%Y-%m-%d") in FERIADOS_PREDETERMINADOS
            )
        })

    return render(request, "calendario.html", {
        "year": year,
        "month": month,
        "dias": dias
    })

@staff_member_required  
def dashboard(request):
    
    total_reservas = Reserva.objects.count()
    pagadas = Reserva.objects.filter(estado="Pagado").count()
    pendientes = Reserva.objects.filter(estado="Pendiente").count()
    canceladas = Reserva.objects.filter(estado="Cancelado").count()

   
    ingresos_totales = 0
    ingresos_por_mes = {} 

    
    reservas_ok = Reserva.objects.filter(estado="Pagado").select_related('cancha')

    for r in reservas_ok:
        if r.hora_inicio and r.hora_fin:
          
            inicio = datetime.combine(date.min, r.hora_inicio)
            fin = datetime.combine(date.min, r.hora_fin)

           
            duracion = fin - inicio
            horas_decimal = duracion.total_seconds() / 3600

            
            monto = int(horas_decimal * float(r.cancha.precio)) 
            
            ingresos_totales += monto

            mes_nombre = r.fecha.strftime("%B %Y").capitalize()
            ingresos_por_mes[mes_nombre] = ingresos_por_mes.get(mes_nombre, 0) + monto

   
    canchas_populares = Reserva.objects.values('cancha__nombre')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:5]

    context = {
        "ingresos_totales": int(ingresos_totales), 
        "pagadas": pagadas,
        "pendientes": pendientes,
        "canceladas": canceladas,
        "ingresos_por_mes": ingresos_por_mes,
        "canchas_populares": canchas_populares,
    }

    return render(request, "dashboard.html", context)