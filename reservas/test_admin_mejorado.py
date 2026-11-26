"""Pruebas de búsqueda, filtros y resúmenes del administrador Django."""

from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from clientes.models import Cliente
from .models import CategoriaEvento, Pago, Reserva, Salon


class AdministradorMejoradoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario_admin = get_user_model().objects.create_superuser(
            username='admin_prueba', email='admin@example.com', password='ClaveDePrueba!2026'
        )
        cls.cliente = Cliente.objects.create(
            nombre='Ana de Prueba', dni='40123456', telefono='3411234567'
        )
        cls.salon, _ = Salon.objects.get_or_create(nombre='El Poli')
        cls.categoria, _ = CategoriaEvento.objects.get_or_create(nombre='Cumpleaños')
        cls.reserva = Reserva.objects.create(
            cliente=cls.cliente, salon=cls.salon, tipo_evento=cls.categoria,
            fecha=date(2026, 12, 15), estado='reservado',
            total=Decimal('100000.00'), pagado_inicial=Decimal('20000.00'),
            cuotas_totales=2,
        )
        cls.pago = Pago.objects.create(
            reserva=cls.reserva, fecha=date(2026, 11, 25),
            monto=Decimal('30000.00'), metodo='transferencia'
        )

    def setUp(self):
        self.client.force_login(self.usuario_admin)

    def test_administrador_de_clientes_permite_buscar_por_dni(self):
        respuesta = self.client.get(reverse('admin:clientes_cliente_changelist'), {'q': '40123456'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['cl'].result_count, 1)
        self.assertContains(respuesta, 'Ana de Prueba')

    def test_administrador_muestra_cantidad_de_reservas_por_cliente(self):
        vista = admin.site._registry[Cliente]
        solicitud = RequestFactory().get('/admin/clientes/cliente/')
        solicitud.user = self.usuario_admin
        cliente = vista.get_queryset(solicitud).get(pk=self.cliente.pk)
        self.assertEqual(vista.cantidad_reservas(cliente), 1)

    def test_administrador_de_reservas_busca_por_dni(self):
        respuesta = self.client.get(reverse('admin:reservas_reserva_changelist'), {'q': '40123456'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['cl'].result_count, 1)

    def test_reserva_muestra_total_pagado_y_saldo_pendiente(self):
        vista = admin.site._registry[Reserva]
        self.assertEqual(vista.total_pagado_admin(self.reserva), Decimal('50000.00'))
        self.assertEqual(vista.saldo_admin(self.reserva), Decimal('50000.00'))

    def test_administrador_de_pagos_filtra_por_metodo(self):
        respuesta = self.client.get(
            reverse('admin:reservas_pago_changelist'), {'metodo__exact': 'transferencia'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['cl'].result_count, 1)

    def test_formulario_de_reserva_permite_buscar_relaciones(self):
        vista = admin.site._registry[Reserva]
        self.assertEqual(vista.autocomplete_fields, ('cliente', 'salon', 'tipo_evento'))
        self.assertContains(
            self.client.get(reverse('admin:reservas_reserva_add')),
            'id_cliente',
        )

    def test_administrador_requiere_usuario_autorizado(self):
        self.client.logout()
        respuesta = self.client.get(reverse('admin:reservas_reserva_changelist'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/admin/login/', respuesta['Location'])
