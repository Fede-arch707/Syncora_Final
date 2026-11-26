"""Pruebas del CRUD de reservas de Syncora.

Ejecutar desde la carpeta que contiene manage.py:
    python manage.py test reservas.test_crud_reservas

Django crea una base de datos temporal para las pruebas.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from .models import CategoriaEvento, Pago, Reserva, Salon


class CrudReservasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='gestor_crud', password='ClaveDePrueba!2027'
        )
        cls.cliente = Cliente.objects.create(nombre='Cliente de prueba', dni='40987654')
        cls.salon, _ = Salon.objects.get_or_create(nombre='El Poli', defaults={'activo': True})
        cls.categoria, _ = CategoriaEvento.objects.get_or_create(nombre='Cumpleaños')

    def setUp(self):
        self.client.force_login(self.usuario)

    def datos_formulario(self, **cambios):
        datos = {
            'cliente': self.cliente.pk,
            'salon': self.salon.pk,
            'fecha': '2027-06-10',
            'tipo_evento': self.categoria.pk,
            'estado': 'reservado',
            'total': '50000.00',
            'cuotas_totales': '2',
            'pagado_inicial': '10000.00',
            'notas': 'Prueba automática',
        }
        datos.update(cambios)
        return datos

    def crear_reserva(self, **cambios):
        datos = {
            'cliente': self.cliente,
            'salon': self.salon,
            'tipo_evento': self.categoria,
            'fecha': date(2027, 6, 10),
            'estado': 'reservado',
            'total': Decimal('50000.00'),
            'cuotas_totales': 2,
            'pagado_inicial': Decimal('10000.00'),
            'notas': 'Prueba automática',
        }
        datos.update(cambios)
        return Reserva.objects.create(**datos)

    def test_01_formulario_de_creacion_se_abre(self):
        respuesta = self.client.get(reverse('reserva_crear'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'reservas/formulario.html')
        self.assertIn('form', respuesta.context)

    def test_02_crear_reserva_guarda_datos_y_redirige(self):
        respuesta = self.client.post(reverse('reserva_crear'), self.datos_formulario())
        self.assertRedirects(respuesta, reverse('calendario'))
        self.assertEqual(Reserva.objects.count(), 1)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.cliente_id, self.cliente.pk)
        self.assertEqual(reserva.salon_id, self.salon.pk)
        self.assertEqual(reserva.fecha, date(2027, 6, 10))
        self.assertEqual(reserva.saldo, Decimal('40000.00'))

    def test_03_creacion_invalida_no_guarda(self):
        respuesta = self.client.post(
            reverse('reserva_crear'), self.datos_formulario(fecha='')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('fecha', respuesta.context['form'].errors)
        self.assertFalse(Reserva.objects.exists())

    def test_04_consultar_detalle_existente(self):
        reserva = self.crear_reserva()
        respuesta = self.client.get(reverse('reserva_detalle', args=[reserva.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'reservas/detalle.html')
        self.assertEqual(respuesta.context['reserva'].pk, reserva.pk)
        self.assertContains(respuesta, 'Cliente de prueba')

    def test_05_edicion_muestra_datos_existentes(self):
        reserva = self.crear_reserva()
        respuesta = self.client.get(reverse('reserva_editar', args=[reserva.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['form'].instance.pk, reserva.pk)
        self.assertTemplateUsed(respuesta, 'reservas/formulario.html')

    def test_06_editar_actualiza_sin_duplicar(self):
        reserva = self.crear_reserva()
        respuesta = self.client.post(
            reverse('reserva_editar', args=[reserva.pk]),
            self.datos_formulario(
                fecha='2027-06-12', estado='alquilado', total='60000.00',
                cuotas_totales='3', notas='Reserva editada'
            ),
        )
        self.assertRedirects(respuesta, reverse('reserva_detalle', args=[reserva.pk]))
        reserva.refresh_from_db()
        self.assertEqual(reserva.fecha, date(2027, 6, 12))
        self.assertEqual(reserva.estado, 'alquilado')
        self.assertEqual(reserva.total, Decimal('60000.00'))
        self.assertEqual(reserva.notas, 'Reserva editada')
        self.assertEqual(Reserva.objects.count(), 1)

    def test_07_edicion_con_fecha_ocupada_se_rechaza(self):
        original = self.crear_reserva(fecha=date(2027, 6, 11))
        ocupante = self.crear_reserva(fecha=date(2027, 6, 12))
        respuesta = self.client.post(
            reverse('reserva_editar', args=[original.pk]),
            self.datos_formulario(fecha='2027-06-12'),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('fecha', respuesta.context['form'].errors)
        original.refresh_from_db()
        self.assertEqual(original.fecha, date(2027, 6, 11))
        self.assertEqual(Reserva.objects.count(), 2)
        self.assertTrue(Reserva.objects.filter(pk=ocupante.pk).exists())

    def test_08_abrir_ruta_de_borrado_no_elimina(self):
        reserva = self.crear_reserva()
        respuesta = self.client.get(reverse('reserva_borrar', args=[reserva.pk]))
        self.assertRedirects(respuesta, reverse('reserva_detalle', args=[reserva.pk]))
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())

    def test_09_borrar_por_post_elimina_reserva_y_sus_pagos(self):
        reserva = self.crear_reserva()
        Pago.objects.create(
            reserva=reserva, fecha=date(2027, 6, 2),
            monto=Decimal('5000.00'), metodo='efectivo'
        )
        respuesta = self.client.post(reverse('reserva_borrar', args=[reserva.pk]))
        self.assertRedirects(respuesta, reverse('calendario'))
        self.assertFalse(Reserva.objects.filter(pk=reserva.pk).exists())
        self.assertEqual(Pago.objects.count(), 0)
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

    def test_10_detalle_de_reserva_inexistente_devuelve_404(self):
        respuesta = self.client.get(reverse('reserva_detalle', args=[999999]))
        self.assertEqual(respuesta.status_code, 404)
