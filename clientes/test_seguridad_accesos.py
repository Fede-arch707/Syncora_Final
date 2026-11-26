"""Pruebas de protección de rutas, acciones HTTP y acceso al administrador.

Estas pruebas usan la base temporal de Django y no modifican db.sqlite3.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from clientes.models import Cliente
from reservas.models import Pago, Reserva, Salon


class SeguridadAccesosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='gestor_seguridad', password='ClaveSegura#2026'
        )
        cls.cliente = Cliente.objects.create(
            nombre='Cliente de prueba', dni='40123456'
        )
        cls.salon = Salon.objects.get(nombre='El Poli')
        cls.reserva = Reserva.objects.create(
            cliente=cls.cliente,
            salon=cls.salon,
            fecha=date(2027, 5, 10),
            estado='reservado',
            total=Decimal('50000.00'),
            cuotas_totales=2,
            pagado_inicial=Decimal('10000.00'),
        )

    def comprobar_redireccion_al_login(self, respuesta):
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta['Location'].startswith(reverse('login')))
        self.assertIn('next=', respuesta['Location'])

    def test_ficha_de_cliente_requiere_login(self):
        respuesta = self.client.get(reverse('cliente_detalle', args=[self.cliente.pk]))
        self.comprobar_redireccion_al_login(respuesta)

    def test_detalle_de_reserva_requiere_login(self):
        respuesta = self.client.get(reverse('reserva_detalle', args=[self.reserva.pk]))
        self.comprobar_redireccion_al_login(respuesta)

    def test_no_se_puede_crear_cliente_sin_login(self):
        respuesta = self.client.post(reverse('cliente_crear'), {
            'nombre': 'No autorizado', 'dni': '40999888',
        })
        self.comprobar_redireccion_al_login(respuesta)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_no_se_puede_crear_reserva_sin_login(self):
        respuesta = self.client.post(reverse('reserva_crear'), {
            'cliente': self.cliente.pk, 'salon': self.salon.pk,
            'fecha': '2027-05-11', 'estado': 'reservado',
            'total': '25000.00', 'cuotas_totales': '1',
            'pagado_inicial': '0.00',
        })
        self.comprobar_redireccion_al_login(respuesta)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_no_se_puede_registrar_pago_sin_login(self):
        respuesta = self.client.post(reverse('pago_crear', args=[self.reserva.pk]), {
            'fecha': '2027-05-01', 'monto': '20000.00', 'metodo': 'efectivo',
        })
        self.comprobar_redireccion_al_login(respuesta)
        self.assertFalse(Pago.objects.exists())

    def test_usuario_comun_no_accede_al_administrador(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('admin:index'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/admin/login/', respuesta['Location'])

    def test_cerrar_sesion_bloquea_nuevamente_el_calendario(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('calendario')).status_code, 200)
        respuesta = self.client.post(reverse('logout'))
        self.assertRedirects(respuesta, reverse('login'))
        self.comprobar_redireccion_al_login(self.client.get(reverse('calendario')))

    def test_no_se_puede_eliminar_cliente_mediante_get(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('cliente_borrar', args=[self.cliente.pk]))
        self.assertRedirects(respuesta, reverse('cliente_detalle', args=[self.cliente.pk]))
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

    def test_crear_reserva_por_post_requiere_token_csrf(self):
        navegador = Client(enforce_csrf_checks=True)
        navegador.force_login(self.usuario)
        respuesta = navegador.post(reverse('reserva_crear'), {
            'cliente': self.cliente.pk, 'salon': self.salon.pk,
            'fecha': '2027-05-12', 'estado': 'reservado',
            'total': '25000.00', 'cuotas_totales': '1',
            'pagado_inicial': '0.00',
        })
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Reserva.objects.count(), 1)
