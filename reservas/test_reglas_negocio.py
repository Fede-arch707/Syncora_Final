"""Pruebas adicionales de reglas de negocio para El Poli / Syncora.

Ejecutar desde la carpeta que contiene manage.py:
    python manage.py test reservas.test_reglas_negocio
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from .forms import ReservaForm
from .models import Pago, Reserva, Salon


class ReglasDeNegocioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_pruebas", password="PruebasSeguras2026!"
        )
        cls.cliente = Cliente.objects.create(
            nombre="Cliente de prueba", dni="40111222"
        )
        cls.salon_a = Salon.objects.create(nombre="Salón de pruebas A")
        cls.salon_b = Salon.objects.create(nombre="Salón de pruebas B")

    def crear_reserva(self, **datos_extra):
        datos = {
            "cliente": self.cliente,
            "salon": self.salon_a,
            "fecha": date(2026, 12, 20),
            "estado": "reservado",
            "total": Decimal("10000.00"),
            "cuotas_totales": 2,
            "pagado_inicial": Decimal("2000.00"),
        }
        datos.update(datos_extra)
        return Reserva.objects.create(**datos)

    def test_dos_salones_pueden_reservarse_el_mismo_dia(self):
        """Evita bloquear todos los salones cuando solamente uno está ocupado."""
        self.crear_reserva()
        formulario = ReservaForm(data={
            "cliente": self.cliente.pk,
            "salon": self.salon_b.pk,
            "fecha": "2026-12-20",
            "estado": "reservado",
            "total": "5000.00",
            "cuotas_totales": "1",
            "pagado_inicial": "0.00",
        })
        self.assertTrue(formulario.is_valid(), formulario.errors.as_text())
        formulario.save()
        self.assertEqual(Reserva.objects.filter(fecha=date(2026, 12, 20)).count(), 2)

    def test_pago_superior_al_saldo_se_rechaza(self):
        """Una deuda de $8.000 no puede recibir un pago de $8.000,01."""
        reserva = self.crear_reserva()
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse("pago_crear", args=[reserva.pk]), {
            "fecha": "2026-12-15",
            "monto": "8000.01",
            "metodo": "efectivo",
            "nota": "Pago inválido de prueba",
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Pago.objects.filter(reserva=reserva).count(), 0)
        self.assertEqual(reserva.saldo, Decimal("8000.00"))

    def test_pago_exactamente_igual_al_saldo_se_acepta(self):
        """Pagar el saldo completo debe dejar la deuda en cero."""
        reserva = self.crear_reserva()
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse("pago_crear", args=[reserva.pk]), {
            "fecha": "2026-12-15",
            "monto": "8000.00",
            "metodo": "transferencia",
            "nota": "Saldo completo",
        })
        self.assertRedirects(respuesta, reverse("reserva_detalle", args=[reserva.pk]))
        self.assertEqual(Pago.objects.filter(reserva=reserva).count(), 1)
        self.assertEqual(reserva.saldo, Decimal("0.00"))

    def test_pago_inicial_no_puede_superar_el_total(self):
        """Un pago inicial mayor al valor del evento debe invalidar el formulario."""
        formulario = ReservaForm(data={
            "cliente": self.cliente.pk,
            "salon": self.salon_a.pk,
            "fecha": "2026-12-21",
            "estado": "reservado",
            "total": "5000.00",
            "cuotas_totales": "2",
            "pagado_inicial": "6000.00",
        })
        self.assertFalse(formulario.is_valid())
        self.assertIn("pagado_inicial", formulario.errors)
        self.assertEqual(Reserva.objects.count(), 0)
