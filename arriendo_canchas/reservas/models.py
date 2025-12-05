from django.db import models
from django.contrib.auth.models import User


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Cancha(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to="canchas/", blank=True, null=True) 

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"



class Reserva(models.Model):

    ESTADOS = [
        ("Pendiente", "Pendiente"),
        ("Pagado", "Pagado"),
        ("Cancelado", "Cancelado"),
    ]

    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    fecha = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="Pendiente")

    def __str__(self):
        return f"{self.cancha} - {self.fecha} {self.hora_inicio} → {self.hora_fin}"


class Log(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)


class FechasNoDisponibles(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Fecha no disponible"
        verbose_name_plural = "Fechas no disponibles"

    def __str__(self):
        return f"{self.cancha.nombre} — {self.fecha_inicio} → {self.fecha_fin}"

    def contiene(self, fecha_obj):
        return self.fecha_inicio <= fecha_obj <= self.fecha_fin
