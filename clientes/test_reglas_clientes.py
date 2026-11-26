"""Pruebas de clientes e historial de reservas para El Poli."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Cliente
from reservas.models import Reserva, Salon


class ReglasClientesTests(TestCase):
    def test_un_mismo_cliente_puede_reservar_varias_veces(self):
        """Reutilizar la ficha del cliente conserva el historial de alquileres."""
        cliente = Cliente.objects.create(nombre='Marta Perez', dni='40123456')
        salon = Salon.objects.create(nombre='Salon de pruebas')

        for fecha in (date(2027, 1, 10), date(2027, 2, 10)):
            Reserva.objects.create(
                cliente=cliente,
                salon=salon,
                fecha=fecha,
                estado='reservado',
                total=Decimal('100000.00'),
                cuotas_totales=2,
                pagado_inicial=Decimal('20000.00'),
            )

        self.assertEqual(Cliente.objects.filter(dni='40123456').count(), 1)
        self.assertEqual(cliente.reservas.count(), 2)
        self.assertEqual(
            list(cliente.reservas.values_list('fecha', flat=True)),
            [date(2027, 1, 10), date(2027, 2, 10)],
        )

    def test_dni_rechaza_letras(self):
        cliente = Cliente(nombre='Marta Perez', dni='40ABC456')

        with self.assertRaises(ValidationError) as error:
            cliente.full_clean()
        self.assertIn('dni', error.exception.message_dict)

    def test_dni_rechaza_longitudes_fuera_del_rango(self):
        for dni in ('123456', '123456789012'):
            with self.subTest(dni=dni):
                cliente = Cliente(nombre='Marta Perez', dni=dni)
                with self.assertRaises(ValidationError) as error:
                    cliente.full_clean()
                self.assertIn('dni', error.exception.message_dict)

    def test_clientes_ordenados_alfabeticamente(self):
        for nombre, dni in (
            ('Zoe', '40111001'),
            ('Marta', '40111002'),
            ('Ana', '40111003'),
        ):
            Cliente.objects.create(nombre=nombre, dni=dni)

        self.assertEqual(
            list(Cliente.objects.values_list('nombre', flat=True)),
            ['Ana', 'Marta', 'Zoe'],
        )
