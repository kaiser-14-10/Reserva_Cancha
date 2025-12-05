from django.contrib import admin
from .models import Cancha, Categoria, Reserva, FechasNoDisponibles

@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "disponible")
    list_filter = ("categoria", "disponible")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("cancha", "usuario", "fecha", "hora_inicio", "hora_fin", "estado")
    list_filter = ("estado", "fecha")


@admin.register(FechasNoDisponibles)
class FechasNoDisponiblesAdmin(admin.ModelAdmin):
    list_display = ("cancha", "fecha_inicio", "fecha_fin", "motivo")
    list_filter = ("cancha",)
