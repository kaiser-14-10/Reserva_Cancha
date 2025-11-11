from django.db import models
from django.contrib.auth.models import User

class Cancha(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    ESTADOS = [('Reservado', 'Reservado'), ('Cancelado', 'Cancelado')]
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Reservado')

    def __str__(self):
        return f"{self.cancha} - {self.fecha} {self.hora}"

class Log(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)
