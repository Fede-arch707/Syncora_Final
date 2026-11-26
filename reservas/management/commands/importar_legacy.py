"""Importa los datos del scale_up.db original sin importar cuentas con claves sin hash."""
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from clientes.models import Cliente
from reservas.models import Salon, Reserva


class Command(BaseCommand):
    help = 'Importa clientes y reservas del archivo SQLite de la versión Flask; nunca importa contraseñas.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta al scale_up.db original')

    def handle(self, *args, **options):
        ruta = Path(options['archivo']).resolve()
        if not ruta.is_file():
            raise CommandError(f'Archivo inexistente: {ruta}')
        with sqlite3.connect(f'{ruta.as_uri()}?mode=ro', uri=True) as db:
            try:
                clientes = db.execute('SELECT id, nombre, dni, telefono, direccion, observaciones FROM clientes').fetchall()
                reservas = db.execute('SELECT id, fecha, cliente_id, total, cuotas_totales, saldo, estado FROM reservas ORDER BY id').fetchall()
            except sqlite3.DatabaseError as error:
                raise CommandError(f'No se reconoce la base de datos de El Poli: {error}') from error
        salon, _ = Salon.objects.get_or_create(nombre='El Poli')
        creados_clientes = 0
        creadas_reservas = 0
        fallidas = 0
        mapa = {}
        with transaction.atomic():
            for legacy_id, nombre, dni, telefono, direccion, obs in clientes:
                dni = str(dni).strip()
                if not dni or not nombre:
                    fallidas += 1
                    continue
                cliente, creado = Cliente.objects.get_or_create(dni=dni, defaults={
                    'nombre': nombre, 'telefono': telefono or '',
                    'direccion': direccion or '', 'observaciones': obs or '',
                })
                mapa[legacy_id] = cliente
                creados_clientes += int(creado)
            for legacy_id, fecha, legacy_cliente, total, cuotas, saldo, estado in reservas:
                cliente = mapa.get(legacy_cliente)
                try:
                    fecha_normalizada = date.fromisoformat(fecha)
                    total_dec = Decimal(str(total)).quantize(Decimal('0.01'))
                    saldo_dec = Decimal(str(saldo)).quantize(Decimal('0.01'))
                except (TypeError, ValueError, InvalidOperation):
                    fallidas += 1
                    continue
                if cliente is None or total_dec <= 0:
                    fallidas += 1
                    continue
                saldo_dec = max(Decimal('0'), min(saldo_dec, total_dec))
                reserva, creada = Reserva.objects.get_or_create(
                    legacy_id=legacy_id, defaults={
                        'salon': salon, 'cliente': cliente, 'fecha': fecha_normalizada,
                        'total': total_dec, 'cuotas_totales': max(int(cuotas or 1), 1),
                        'pagado_inicial': total_dec - saldo_dec,
                        'estado': estado if estado in ('reservado', 'alquilado') else 'reservado',
                    },
                )
                creadas_reservas += int(creada)
        self.stdout.write(self.style.SUCCESS(
            f'Importación terminada: {creados_clientes} clientes y {creadas_reservas} reservas nuevas. {fallidas} registros omitidos.'
        ))
        self.stdout.write('No se importaron usuarios ni contraseñas de Flask. Creá cuentas nuevas en /registro/ o con createsuperuser.')
        self.stdout.write('Revisá fechas repetidas en el calendario: se conservaron como historial, sin eliminar registros.')
