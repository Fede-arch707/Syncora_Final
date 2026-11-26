from django.core.validators import RegexValidator
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    dni = models.CharField(
        max_length=16, unique=True,
        validators=[RegexValidator(r'^\d{7,11}$', 'Ingresá de 7 a 11 dígitos, sin puntos.')],
    )
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    vetado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'

    def __str__(self):
        return f'{self.nombre} ({self.dni})'
