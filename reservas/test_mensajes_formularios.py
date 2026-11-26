"""Pruebas de los mensajes que recibe el usuario al completar formularios."""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from .models import Pago, Reserva, Salon


class MensajesDeFormulariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user('pruebas_formularios', password='ClavePrueba!2026')
        cls.cliente = Cliente.objects.create(nombre='Cliente de prueba', dni='40123456')
        cls.salon = Salon.objects.get(nombre='El Poli')

    def setUp(self):
        self.client.force_login(self.usuario)

    def datos_reserva(self, fecha='2027-01-10', cliente=None):
        return {
            'cliente': cliente or self.cliente.pk,
            'salon': self.salon.pk,
            'fecha': fecha,
            'estado': 'reservado',
            'total': '100000.00',
            'cuotas_totales': '2',
            'pagado_inicial': '20000.00',
        }

    def test_dni_duplicado_indica_usar_ficha_existente(self):
        respuesta = self.client.post(reverse('cliente_crear'), {
            'nombre': 'Cliente duplicado', 'dni': self.cliente.dni,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Este DNI ya está registrado.')
        self.assertContains(respuesta, 'Revisá los datos indicados abajo.')
        self.assertEqual(Cliente.objects.filter(dni=self.cliente.dni).count(), 1)

    def test_dni_con_letras_muestra_formato_correcto(self):
        respuesta = self.client.post(reverse('cliente_crear'), {
            'nombre': 'Cliente nuevo', 'dni': 'DNI1234',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ingresá de 7 a 11 dígitos, sin puntos.')
        self.assertFalse(Cliente.objects.filter(nombre='Cliente nuevo').exists())

    def test_mismo_cliente_puede_reservar_dos_fechas(self):
        for fecha in ('2027-01-10', '2027-01-11'):
            respuesta = self.client.post(reverse('reserva_crear'), self.datos_reserva(fecha))
            self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Reserva.objects.filter(cliente=self.cliente).count(), 2)

    def test_reserva_duplicada_muestra_mensaje_entendible(self):
        Reserva.objects.create(
            cliente=self.cliente, salon=self.salon, fecha=date(2027, 1, 10),
            total=Decimal('100000.00'),
        )
        respuesta = self.client.post(reverse('reserva_crear'), self.datos_reserva())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Este salón ya tiene una reserva en esa fecha.')
        self.assertContains(respuesta, 'No se pudo guardar la reserva.')
        self.assertEqual(Reserva.objects.count(), 1)

    def test_cliente_vetado_muestra_por_que_no_puede_reservar(self):
        self.cliente.vetado = True
        self.cliente.save()
        respuesta = self.client.post(reverse('reserva_crear'), self.datos_reserva())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'El cliente está vetado y no puede reservar.')
        self.assertEqual(Reserva.objects.count(), 0)

    def test_pago_superior_al_saldo_muestra_error_y_no_se_guarda(self):
        reserva = Reserva.objects.create(
            cliente=self.cliente, salon=self.salon, fecha=date(2027, 1, 12),
            total=Decimal('100000.00'), pagado_inicial=Decimal('20000.00'),
        )
        respuesta = self.client.post(reverse('pago_crear', args=[reserva.pk]), {
            'fecha': '2027-01-12', 'monto': '90000.00', 'metodo': 'efectivo',
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertContains(respuesta, 'El pago supera el saldo pendiente.', status_code=400)
        self.assertContains(respuesta, 'No se pudo registrar el pago.', status_code=400)
        self.assertEqual(Pago.objects.filter(reserva=reserva).count(), 0)
