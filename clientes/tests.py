from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Cliente
from reservas.models import Salon, Reserva


class ClientesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='gestor', password='ClaveSegura!2026')

    def test_el_panel_exige_login(self):
        respuesta = self.client.get(reverse('calendario'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('login', respuesta['Location'])

    def test_registro_crea_usuario_e_inicia_sesion(self):
        respuesta = self.client.post(reverse('registro'), {
            'username': 'otro_gestor', 'email': 'demo@example.com',
            'password1': 'ClaveDeEjemplo!2026', 'password2': 'ClaveDeEjemplo!2026',
        })
        self.assertRedirects(respuesta, reverse('calendario'))
        self.assertTrue(User.objects.filter(username='otro_gestor').exists())

    def test_crear_cliente_y_validar_dni_unico(self):
        self.client.force_login(self.user)
        datos = {'nombre': 'Marta González', 'dni': '40123456', 'telefono': '34111111',
                 'direccion': 'Calle 12', 'observaciones': 'Cumpleaños'}
        respuesta = self.client.post(reverse('cliente_crear'), datos)
        self.assertRedirects(respuesta, reverse('calendario'))
        self.assertEqual(Cliente.objects.count(), 1)
        respuesta = self.client.post(reverse('cliente_crear'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Cliente', status_code=200)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_no_se_elimina_cliente_con_reservas(self):
        self.client.force_login(self.user)
        cliente = Cliente.objects.create(nombre='Marta', dni='40000111')
        Reserva.objects.create(cliente=cliente, salon=Salon.objects.get(nombre='El Poli'),
                               fecha='2026-12-18', estado='reservado', total='10000.00', cuotas_totales=2)
        self.client.post(reverse('cliente_borrar', args=[cliente.pk]))
        self.assertTrue(Cliente.objects.filter(pk=cliente.pk).exists())


class ExportarExcelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from decimal import Decimal
        from datetime import date
        from reservas.models import Pago
        cls.usuario = User.objects.create_user(username='excel_user', password='ClaveExcel!2026')
        cls.cliente = Cliente.objects.create(nombre='=Cliente Peligroso', dni='45123456', observaciones='Observación de prueba')
        cls.sin_reserva = Cliente.objects.create(nombre='Sin reserva', dni='41234567', vetado=True)
        salon = Salon.objects.get(nombre='El Poli')
        for numero, dia in enumerate((14, 21), start=1):
            r = Reserva.objects.create(
                cliente=cls.cliente, salon=salon, fecha=date(2026, 12, dia),
                estado='reservado', total=Decimal('100000.00'), cuotas_totales=2,
                pagado_inicial=Decimal('20000.00'),
            )
            if numero == 1:
                Pago.objects.create(reserva=r, fecha=date(2026, 11, 22), monto=Decimal('30000.00'))

    def test_exportar_requiere_autenticacion(self):
        url = reverse('clientes_exportar_excel')
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('login', respuesta['Location'])

    def test_exportar_es_xlsx_valido_con_historial_y_pagos(self):
        from io import BytesIO
        from zipfile import ZipFile
        import xml.etree.ElementTree as ET
        url = reverse('clientes_exportar_excel')
        self.client.force_login(self.usuario)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('spreadsheetml.sheet', respuesta['Content-Type'])
        self.assertIn('.xlsx', respuesta['Content-Disposition'])
        with ZipFile(BytesIO(respuesta.content)) as archivo:
            self.assertIsNone(archivo.testzip())
            assert {'xl/workbook.xml', 'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml'} <= set(archivo.namelist())
            raiz = ET.fromstring(archivo.read('xl/worksheets/sheet1.xml'))
            ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            filas = raiz.findall('m:sheetData/m:row', ns)
            self.assertEqual(len(filas), 4)  # Encabezado + 2 reservas + cliente sin reservas
            textos = [n.text for n in raiz.findall('.//m:t', ns)]
            self.assertIn('=Cliente Peligroso', textos)
            self.assertIn('Sin reserva', textos)
            pagos = ET.fromstring(archivo.read('xl/worksheets/sheet2.xml'))
            self.assertEqual(len(pagos.findall('m:sheetData/m:row', ns)), 4)  # Encabezado + dos iniciales + un pago
        self.assertEqual(Cliente.objects.count(), 2)
        self.assertEqual(Reserva.objects.count(), 2)
