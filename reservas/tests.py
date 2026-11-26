from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from clientes.models import Cliente
from .forms import ReservaForm
from .models import Reserva, Pago, Salon


class ReservasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='gestor', password='ClaveSegura!2026')
        cls.salon = Salon.objects.get(nombre='El Poli')
        cls.cliente = Cliente.objects.create(nombre='Ana López', dni='40888777')

    def test_creacion_y_consulta_de_reserva(self):
        self.client.force_login(self.user)
        respuesta = self.client.post(reverse('reserva_crear'), {
            'cliente': self.cliente.pk, 'salon': self.salon.pk,
            'fecha': '2026-12-05', 'estado': 'reservado',
            'total': '30000.00', 'cuotas_totales': '3', 'pagado_inicial': '10000.00',
        })
        self.assertRedirects(respuesta, reverse('calendario'))
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.saldo, Decimal('20000.00'))
        self.assertContains(self.client.get(reverse('reserva_detalle', args=[reserva.pk])), 'Ana López')

    def test_no_permite_doble_reserva(self):
        Reserva.objects.create(cliente=self.cliente, salon=self.salon, fecha='2026-12-06',
                               estado='reservado', total=1000, cuotas_totales=1)
        form = ReservaForm(data={
            'cliente': self.cliente.pk, 'salon': self.salon.pk, 'fecha': '2026-12-06',
            'estado': 'reservado', 'total': 1000, 'cuotas_totales': 1, 'pagado_inicial': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fecha', form.errors)

    def test_vetados_no_reservan(self):
        self.cliente.vetado = True
        self.cliente.save()
        form = ReservaForm(data={
            'cliente': self.cliente.pk, 'salon': self.salon.pk, 'fecha': '2026-12-07',
            'estado': 'reservado', 'total': 1000, 'cuotas_totales': 1, 'pagado_inicial': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('cliente', form.errors)

    def test_pagos_reducen_saldo(self):
        self.client.force_login(self.user)
        reserva = Reserva.objects.create(cliente=self.cliente, salon=self.salon,
                     fecha='2026-12-08', total=Decimal('9000'), pagado_inicial=Decimal('2000'))
        respuesta = self.client.post(reverse('pago_crear', args=[reserva.pk]), {
            'fecha': '2026-12-01', 'monto': '3500.00', 'metodo': 'efectivo', 'nota': 'Segunda cuota',
        })
        self.assertRedirects(respuesta, reverse('reserva_detalle', args=[reserva.pk]))
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(reserva.saldo, Decimal('3500.00'))

    def test_no_se_elimina_reserva_por_get(self):
        self.client.force_login(self.user)
        reserva = Reserva.objects.create(cliente=self.cliente, salon=self.salon,
                                         fecha='2026-12-09', total=1000)
        self.client.get(reverse('reserva_borrar', args=[reserva.pk]))
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())
