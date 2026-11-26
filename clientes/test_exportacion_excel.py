"""Pruebas de la exportación XLSX de El Poli.

Usan únicamente la biblioteca estándar de Python para leer el XML del XLSX.
No requieren Excel ni alteran la base de datos real: Django crea una BD de prueba.
"""
from datetime import date
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from reservas.models import Pago, Reserva, Salon


NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
URL_EXPORTACION = 'clientes_exportar_excel'


def leer_filas(contenido_xlsx, numero_hoja):
    """Devuelve filas como diccionarios columna -> valor, respetando celdas vacías."""
    with ZipFile(BytesIO(contenido_xlsx)) as archivo:
        raiz = ET.fromstring(archivo.read(f'xl/worksheets/sheet{numero_hoja}.xml'))

    filas = []
    for fila_xml in raiz.findall('m:sheetData/m:row', NS):
        fila = {}
        for celda in fila_xml.findall('m:c', NS):
            referencia = celda.attrib['r']
            columna = ''.join(caracter for caracter in referencia if caracter.isalpha())
            if celda.attrib.get('t') == 'inlineStr':
                valor = ''.join(nodo.text or '' for nodo in celda.findall('.//m:t', NS))
            else:
                nodo_valor = celda.find('m:v', NS)
                valor = nodo_valor.text if nodo_valor is not None else ''
            fila[columna] = valor
        filas.append(fila)
    return filas


class ExportacionExcelReglasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='prueba_exportador', password='ClaveDePrueba2026!'
        )
        cls.salon, _ = Salon.objects.get_or_create(nombre='El Poli')
        cls.cliente = Cliente.objects.create(
            nombre='=SUMA(1;2)', dni='40777111', telefono='3415550000',
            observaciones='Cliente frecuente'
        )
        cls.cliente_sin_reservas = Cliente.objects.create(
            nombre='Cliente sin reservas', dni='40777222', vetado=True
        )
        cls.reserva_1 = Reserva.objects.create(
            cliente=cls.cliente, salon=cls.salon, fecha=date(2026, 12, 14),
            estado='reservado', total=Decimal('100000.00'), cuotas_totales=2,
            pagado_inicial=Decimal('20000.00')
        )
        cls.reserva_2 = Reserva.objects.create(
            cliente=cls.cliente, salon=cls.salon, fecha=date(2026, 12, 21),
            estado='alquilado', total=Decimal('100000.00'), cuotas_totales=2,
            pagado_inicial=Decimal('20000.00')
        )
        cls.pago = Pago.objects.create(
            reserva=cls.reserva_1, fecha=date(2026, 12, 2),
            monto=Decimal('30000.00'), metodo='transferencia', nota='Segunda cuota'
        )

    def descargar(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse(URL_EXPORTACION))
        self.assertEqual(respuesta.status_code, 200)
        return respuesta

    def test_sin_sesion_redirige_al_login(self):
        respuesta = self.client.get(reverse(URL_EXPORTACION))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('login', respuesta['Location'])

    def test_descarga_tiene_tipo_nombre_y_cache_privado(self):
        respuesta = self.descargar()
        self.assertEqual(
            respuesta['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('.xlsx', respuesta['Content-Disposition'])
        self.assertIn('attachment', respuesta['Content-Disposition'])
        self.assertIn('no-store', respuesta['Cache-Control'])
        self.assertTrue(respuesta.content.startswith(b'PK'))

    def test_tres_hojas_con_nombres_y_encabezados(self):
        respuesta = self.descargar()
        with ZipFile(BytesIO(respuesta.content)) as archivo:
            self.assertIsNone(archivo.testzip())
            raiz = ET.fromstring(archivo.read('xl/workbook.xml'))
            nombres = [hoja.attrib['name'] for hoja in raiz.findall('m:sheets/m:sheet', NS)]
        self.assertEqual(nombres, ['Clientes y reservas', 'Pagos', 'Información'])
        self.assertEqual(leer_filas(respuesta.content, 1)[0]['C'], 'Nombre')
        self.assertEqual(leer_filas(respuesta.content, 1)[0]['M'], 'Saldo')
        self.assertEqual(leer_filas(respuesta.content, 2)[0]['E'], 'Monto')

    def test_se_conservan_dos_reservas_y_cliente_sin_reserva(self):
        filas = leer_filas(self.descargar().content, 1)[1:]
        self.assertEqual(len(filas), 3)
        historial = [fila for fila in filas if fila.get('C') == self.cliente.nombre]
        self.assertEqual(len(historial), 2)
        self.assertEqual(
            {fila.get('B') for fila in historial},
            {str(self.reserva_1.pk), str(self.reserva_2.pk)}
        )
        sin_reserva = next(fila for fila in filas if fila.get('C') == 'Cliente sin reservas')
        self.assertEqual(sin_reserva.get('B', ''), '')
        self.assertEqual(sin_reserva['H'], 'Sí')

    def test_importes_y_saldos_se_exportan_como_numeros_correctos(self):
        filas = leer_filas(self.descargar().content, 1)[1:]
        por_reserva = {fila.get('B'): fila for fila in filas if fila.get('B')}
        primera = por_reserva[str(self.reserva_1.pk)]
        segunda = por_reserva[str(self.reserva_2.pk)]
        self.assertEqual(Decimal(primera['K']), Decimal('100000.00'))
        self.assertEqual(int(primera['L']), 2)
        self.assertEqual(Decimal(primera['M']), Decimal('50000.00'))
        self.assertEqual(Decimal(segunda['M']), Decimal('80000.00'))
        self.assertEqual(primera['J'], 'Reservado')
        self.assertEqual(segunda['J'], 'Alquilado')

    def test_hoja_pagos_incluye_iniciales_y_transferencia(self):
        filas = leer_filas(self.descargar().content, 2)[1:]
        self.assertEqual(len(filas), 3)  # 2 pagos iniciales + 1 posterior
        iniciales = [fila for fila in filas if fila.get('F') == 'Pago inicial']
        self.assertEqual(len(iniciales), 2)
        self.assertTrue(all(Decimal(fila['E']) == Decimal('20000') for fila in iniciales))
        posterior = next(fila for fila in filas if fila.get('A') == str(self.pago.pk))
        self.assertEqual(posterior['B'], str(self.reserva_1.pk))
        self.assertEqual(Decimal(posterior['E']), Decimal('30000.00'))
        self.assertEqual(posterior['F'], 'Transferencia')
        self.assertEqual(posterior['G'], 'Segunda cuota')

    def test_texto_parecido_a_formula_no_se_ejecuta(self):
        contenido = self.descargar().content
        with ZipFile(BytesIO(contenido)) as archivo:
            raiz = ET.fromstring(archivo.read('xl/worksheets/sheet1.xml'))
        celdas = raiz.findall('.//m:c', NS)
        peligrosas = [c for c in celdas if any(
            (n.text or '') == self.cliente.nombre for n in c.findall('.//m:t', NS)
        )]
        self.assertEqual(len(peligrosas), 2)
        for celda in peligrosas:
            self.assertEqual(celda.attrib.get('t'), 'inlineStr')
            self.assertIsNone(celda.find('m:f', NS))

    def test_exportar_no_modifica_los_registros(self):
        antes = (Cliente.objects.count(), Reserva.objects.count(), Pago.objects.count(),
                 self.reserva_1.saldo, self.reserva_2.saldo)
        self.descargar()
        despues = (Cliente.objects.count(), Reserva.objects.count(), Pago.objects.count(),
                   self.reserva_1.saldo, self.reserva_2.saldo)
        self.assertEqual(despues, antes)


class ExcelSinClientesTests(TestCase):
    def test_exporta_hojas_con_encabezados_aunque_no_haya_clientes(self):
        usuario = get_user_model().objects.create_user(
            username='sin_clientes', password='ClaveDePrueba2026!'
        )
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse(URL_EXPORTACION))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(leer_filas(respuesta.content, 1)), 1)
        self.assertEqual(len(leer_filas(respuesta.content, 2)), 1)
        self.assertGreater(len(leer_filas(respuesta.content, 3)), 1)
