from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Salon(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'salón'
        verbose_name_plural = 'salones'

    def __str__(self):
        return self.nombre


class CategoriaEvento(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría de evento'
        verbose_name_plural = 'categorías de eventos'

    def __str__(self):
        return self.nombre


class Reserva(models.Model):
    ESTADOS = [('reservado', 'Reservado'), ('alquilado', 'Alquilado')]
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='reservas')
    salon = models.ForeignKey(Salon, on_delete=models.PROTECT, related_name='reservas')
    tipo_evento = models.ForeignKey(CategoriaEvento, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    fecha = models.DateField(db_index=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default='reservado')
    total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    cuotas_totales = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    pagado_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    notas = models.TextField(blank=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'

    def __str__(self):
        return f'{self.salon} - {self.fecha} - {self.cliente}'

    @property
    def total_pagado(self):
        return self.pagado_inicial + sum((pago.monto for pago in self.pagos.all()), Decimal('0.00'))

    @property
    def saldo(self):
        return max(self.total - self.total_pagado, Decimal('0.00'))

    @property
    def cantidad_pagos(self):
        return (1 if self.pagado_inicial > 0 else 0) + len(self.pagos.all())

    def clean(self):
        super().clean()
        errores = {}
        if self.total is not None and self.pagado_inicial is not None and self.pagado_inicial > self.total:
            errores['pagado_inicial'] = 'El pago inicial no puede superar el total.'
        existente = Reserva.objects.filter(pk=self.pk).first() if self.pk else None
        if self.cliente_id and self.cliente.vetado and (not existente or existente.cliente_id != self.cliente_id):
            errores['cliente'] = 'El cliente está vetado y no puede reservar.'
        if existente and self.total is not None and self.pagado_inicial is not None and self.total < self.pagado_inicial + sum((p.monto for p in self.pagos.all()), Decimal('0.00')):
            errores['total'] = 'El total no puede ser menor que los pagos ya registrados.'
        if self.fecha and self.salon_id:
            sin_cambio_en_fecha = (existente and existente.legacy_id is not None
                                   and existente.fecha == self.fecha and existente.salon_id == self.salon_id)
            ocupada = Reserva.objects.filter(fecha=self.fecha, salon_id=self.salon_id).exclude(pk=self.pk).exists()
            if ocupada and not sin_cambio_en_fecha:
                errores['fecha'] = 'Este salón ya tiene una reserva en esa fecha.'
        if errores:
            raise ValidationError(errores)


class Pago(models.Model):
    METODOS = [('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'), ('otro', 'Otro')]
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateField(default=timezone.localdate)
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    metodo = models.CharField(max_length=20, choices=METODOS, default='efectivo')
    nota = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['fecha', 'pk']
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'

    def __str__(self):
        return f'{self.monto} - {self.reserva}'

    def clean(self):
        super().clean()
        if self.reserva_id and self.monto and self.pk is None and self.monto > self.reserva.saldo:
            raise ValidationError({'monto': 'El pago supera el saldo pendiente.'})
