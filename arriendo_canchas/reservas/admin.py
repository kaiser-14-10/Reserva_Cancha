from django.contrib import admin
from .models import Cancha, Reserva, Log, FechasNoDisponibles

admin.site.register(Cancha)
admin.site.register(Reserva)
admin.site.register(Log)

@admin.register(FechasNoDisponibles)
class FechasNoDisponiblesAdmin(admin.ModelAdmin):
    list_display = ("cancha", "fecha_inicio", "fecha_fin", "motivo")
    list_filter = ("cancha", "fecha_inicio", "fecha_fin")
    search_fields = ("cancha__nombre", "motivo")


