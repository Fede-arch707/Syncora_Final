"""Exportador Excel (.xlsx) sin dependencias adicionales.

Conserva los encabezados históricos de El Poli y no modifica la base de datos.
Las celdas de texto se guardan como texto real para impedir fórmulas inyectadas.
"""
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

from django.utils import timezone
from clientes.models import Cliente
from reservas.models import Pago, Reserva

MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
ENCABEZADOS = [
    'ID cliente', 'ID reserva', 'Nombre', 'DNI', 'Teléfono', 'Dirección',
    'Observaciones', 'Vetado', 'Fecha', 'Estado', 'Total', 'Cuotas totales', 'Saldo',
]
ENCABEZADOS_PAGOS = ['ID pago', 'ID reserva', 'Cliente', 'Fecha', 'Monto', 'Método', 'Nota']


def _xml_text(value):
    # Aceptar solo caracteres válidos en XML 1.0, sin alterar datos habituales.
    text = str(value)
    text = ''.join(c for c in text if ord(c) in (9, 10, 13) or 32 <= ord(c) <= 0xD7FF
                   or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF)
    return escape(text, {'"': '&quot;', "'": '&apos;'})


def _columna(indice):
    resultado = ''
    while indice:
        indice, resto = divmod(indice - 1, 26)
        resultado = chr(65 + resto) + resultado
    return resultado


def _celda(value, referencia, estilo=0):
    attr = f' r="{referencia}"' + (f' s="{estilo}"' if estilo else '')
    if value is None or value == '':
        return f'<c{attr}/>'
    if isinstance(value, (date, datetime)):
        if isinstance(value, datetime):
            value = value.date()
        # Excel: día 0 = 1899-12-30 (con compatibilidad del salto de 1900).
        return f'<c{attr}><v>{(value - date(1899, 12, 30)).days}</v></c>'
    if isinstance(value, (int, Decimal, float)) and not isinstance(value, bool):
        return f'<c{attr}><v>{value}</v></c>' if not estilo else f'<c{attr}><v>{value}</v></c>'
    # inlineStr => Excel nunca ejecuta nombres/observaciones como fórmulas.
    return f'<c{attr} t="inlineStr"><is><t xml:space="preserve">{_xml_text(value)}</t></is></c>'


def _celda_con_estilo(value, referencia, estilo):
    # La función base escribe los valores; se aplica el estilo a todos los tipos.
    xml = _celda(value, referencia, estilo=0)
    if estilo:
        xml = xml.replace('<c ', f'<c s="{estilo}" ', 1)
    return xml


def _hoja_xml(headers, rows, widths, *, fecha_cols=(), dinero_cols=(), vetado_col=None):
    ncols = len(headers)
    lastrow = len(rows) + 1
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '<sheetViews><sheetView workbookViewId="0"><pane xSplit="2" ySplit="1" topLeftCell="C2" activePane="bottomRight" state="frozen"/><selection pane="bottomRight" activeCell="C2" sqref="C2"/></sheetView></sheetViews>',
        '<sheetFormatPr defaultRowHeight="18"/>',
        '<cols>',
    ]
    for index, width in enumerate(widths, start=1):
        parts.append(f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>')
    parts.append('</cols><sheetData><row r="1" ht="32" customHeight="1">')
    for index, titulo in enumerate(headers, start=1):
        parts.append(_celda_con_estilo(titulo, f'{_columna(index)}1', 1))
    parts.append('</row>')
    for numero, fila in enumerate(rows, start=2):
        parts.append(f'<row r="{numero}">')
        for index, valor in enumerate(fila, start=1):
            if valor is None or valor == '':
                continue
            estilo = 2 if numero % 2 == 0 else 0
            if index in fecha_cols and isinstance(valor, (date, datetime)):
                estilo = 3
            elif index in dinero_cols and isinstance(valor, (Decimal, int, float)):
                estilo = 4
            elif index == vetado_col and valor == 'Sí':
                estilo = 5
            parts.append(_celda_con_estilo(valor, f'{_columna(index)}{numero}', estilo))
        parts.append('</row>')
    parts.append('</sheetData>')
    parts.append(f'<autoFilter ref="A1:{_columna(ncols)}{lastrow}"/>')
    parts.append('<pageMargins left="0.25" right="0.25" top="0.45" bottom="0.45" header="0.2" footer="0.2"/>')
    parts.append('</worksheet>')
    return ''.join(parts).encode('utf-8')


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3">
<font><sz val="11"/><name val="Aptos"/><color rgb="FF24322D"/></font>
<font><b/><sz val="11"/><name val="Aptos"/><color rgb="FFFFFFFF"/></font>
<font><b/><sz val="11"/><name val="Aptos"/><color rgb="FFB42318"/></font>
</fonts>
<fills count="4">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF165F4C"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEDF5F0"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="6">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>
<xf numFmtId="14" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="4" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _estructura(sheets):
    tipos = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
             '<Default Extension="xml" ContentType="application/xml"/>',
             '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
             '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    libro = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    links = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for num, (name, _) in enumerate(sheets, start=1):
        tipos.append(f'<Override PartName="/xl/worksheets/sheet{num}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        libro.append(f'<sheet name="{_xml_text(name)}" sheetId="{num}" r:id="rId{num}"/>')
        links.append(f'<Relationship Id="rId{num}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{num}.xml"/>')
    links.append(f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
    tipos.append('</Types>'); libro.append('</sheets></workbook>'); links.append('</Relationships>')
    paquete = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
               '</Relationships>')
    return ''.join(tipos), ''.join(libro), ''.join(links), paquete


def generar_excel():
    """Construye una instantánea de los datos, incluyendo todas las reservas históricas."""
    clientes = Cliente.objects.order_by('nombre', 'pk').prefetch_related(
        'reservas__pagos', 'reservas__salon', 'reservas__tipo_evento'
    )
    registros = []
    for cliente in clientes:
        reservas = sorted(cliente.reservas.all(), key=lambda item: (item.fecha, item.pk))
        if not reservas:
            registros.append([
                str(cliente.pk), '', cliente.nombre, cliente.dni, cliente.telefono,
                cliente.direccion, cliente.observaciones, 'Sí' if cliente.vetado else 'No',
                None, '', None, None, None,
            ])
        for reserva in reservas:
            registros.append([
                str(cliente.pk), str(reserva.pk), cliente.nombre, cliente.dni,
                cliente.telefono, cliente.direccion,
                reserva.notas or cliente.observaciones, 'Sí' if cliente.vetado else 'No',
                reserva.fecha, reserva.get_estado_display(), reserva.total,
                reserva.cuotas_totales, reserva.saldo,
            ])

    detalle_pagos = []
    # Mostramos el pago inicial junto con cada pago posterior para poder auditar el saldo.
    reservas = Reserva.objects.select_related('cliente').prefetch_related('pagos').order_by('fecha', 'pk')
    for reserva in reservas:
        if reserva.pagado_inicial:
            detalle_pagos.append([
                '', str(reserva.pk), reserva.cliente.nombre, None,
                reserva.pagado_inicial, 'Pago inicial', 'Sin fecha histórica registrada',
            ])
        for pago in reserva.pagos.all():
            detalle_pagos.append([
                str(pago.pk), str(reserva.pk), reserva.cliente.nombre,
                pago.fecha, pago.monto, pago.get_metodo_display(), pago.nota,
            ])

    filas_info = [
        ['EL POLI · EXPORTACIÓN DE DATOS', ''],
        ['Fecha de exportación', timezone.localdate().isoformat()],
        ['Clientes y reservas', 'Una fila por reserva; clientes sin reservas aparecen igualmente.'],
        ['Historial', 'Si un cliente reservó varias veces, aparece en varias filas. No se eliminan fechas anteriores.'],
        ['Saldo', 'Total menos pago inicial y pagos registrados.'],
        ['Pagos', 'La hoja Pagos incluye pagos iniciales y pagos posteriores; el pago inicial puede no tener fecha histórica.'],
        ['Seguridad', 'El archivo contiene datos personales: guardalo en un lugar seguro y compartilo solo con autorización.'],
        ['Nota', 'Exportar no modifica ni borra la información del programa.'],
    ]
    hojas = [
        ('Clientes y reservas', _hoja_xml(ENCABEZADOS, registros,
          [16, 16, 30, 18, 22, 35, 45, 12, 17, 18, 19, 18, 19],
          fecha_cols=(9,), dinero_cols=(11, 13), vetado_col=8)),
        ('Pagos', _hoja_xml(ENCABEZADOS_PAGOS, detalle_pagos,
          [16, 18, 30, 19, 20, 22, 46], fecha_cols=(4,), dinero_cols=(5,))),
        ('Información', _hoja_xml(['Tema', 'Detalle'], filas_info, [38, 100])),
    ]
    tipos, libro, links, paquete = _estructura(hojas)
    salida = BytesIO()
    with ZipFile(salida, 'w', compression=ZIP_DEFLATED) as zipfile:
        zipfile.writestr('[Content_Types].xml', tipos)
        zipfile.writestr('_rels/.rels', paquete)
        zipfile.writestr('xl/workbook.xml', libro)
        zipfile.writestr('xl/_rels/workbook.xml.rels', links)
        zipfile.writestr('xl/styles.xml', STYLES)
        for n, (_, cuerpo) in enumerate(hojas, start=1):
            zipfile.writestr(f'xl/worksheets/sheet{n}.xml', cuerpo)
    return salida.getvalue()
