from django.contrib import admin
from .models import Cancha, Categoria, Reserva, FechasNoDisponibles, Log

@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "disponible")
    list_filter = ("categoria", "disponible")
    search_fields = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("cancha", "usuario", "fecha", "hora_inicio", "hora_fin", "estado")
    list_filter = ("estado", "fecha", "cancha")
    search_fields = ("usuario__username", "cancha__nombre")


@admin.register(FechasNoDisponibles)
class FechasNoDisponiblesAdmin(admin.ModelAdmin):
    list_display = ("cancha", "fecha_inicio", "fecha_fin", "motivo")
    list_filter = ("cancha", "fecha_inicio")
    search_fields = ("motivo",)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("usuario", "accion", "fecha")
    list_filter = ("fecha",)
    search_fields = ("usuario__username", "accion")
