from django.contrib import admin
from django import forms
from datetime import time

from .models import (
    Cancha, Categoria, Reserva,
    HorasNoDisponibles, DiaBloqueado
)


HORAS_DISPONIBLES = [
    time(9, 0), time(9, 30),
    time(10, 0), time(10, 30),
    time(11, 0), time(11, 30),
    time(12, 0), time(12, 30),
    time(13, 0), time(13, 30),
    time(14, 0), time(14, 30),
    time(15, 0), time(15, 30),
    time(16, 0), time(16, 30),
    time(17, 0), time(17, 30),
    time(18, 0), time(18, 30),
    time(19, 0), time(19, 30),
    time(20, 0), time(20, 30),
    time(21, 0), time(21, 30),
    time(22, 0),
]

HOUR_CHOICES = [(h.strftime("%H:%M"), h.strftime("%H:%M")) for h in HORAS_DISPONIBLES]



class HorasNoDisponiblesForm(forms.ModelForm):
    hora_inicio = forms.ChoiceField(
        choices=HOUR_CHOICES,
        label="Hora inicio",
        required=True
    )
    hora_fin = forms.ChoiceField(
        choices=HOUR_CHOICES,
        label="Hora fin",
        required=True
    )

    class Meta:
        model = HorasNoDisponibles
        fields = ("cancha", "fecha", "hora_inicio", "hora_fin", "motivo")

    def clean(self):
        cleaned = super().clean()

        h_ini = cleaned.get("hora_inicio")
        h_fin = cleaned.get("hora_fin")

        if h_ini and h_fin:
            hi = time.fromisoformat(h_ini)
            hf = time.fromisoformat(h_fin)

            if hi >= hf:
                raise forms.ValidationError(
                    "La hora fin debe ser mayor que la hora inicio."
                )

        return cleaned



@admin.register(HorasNoDisponibles)
class HorasNoDisponiblesAdmin(admin.ModelAdmin):
    form = HorasNoDisponiblesForm
    list_display = ("cancha", "fecha", "hora_inicio", "hora_fin", "motivo")
    list_filter = ("cancha", "fecha")
    ordering = ("fecha", "hora_inicio")


@admin.register(DiaBloqueado)
class DiaBloqueadoAdmin(admin.ModelAdmin):
    list_display = ("cancha", "fecha", "motivo")
    list_filter = ("cancha", "fecha")


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "disponible")
    list_filter = ("categoria", "disponible")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "cancha",
        "usuario",
        "fecha",
        "hora_inicio",
        "hora_fin",
        "estado"
    )
    list_filter = ("estado", "fecha", "cancha")

