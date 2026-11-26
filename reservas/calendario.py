import calendar

MESES_ES = ('Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
            'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')


def generar_calendario(anio, reservas):
    """Prepara meses y días para el template, sin decisiones de negocio."""
    por_fecha = {reserva.fecha.isoformat(): reserva for reserva in reservas}
    meses = []
    for mes_num in range(1, 13):
        dias = []
        for semana in calendar.monthcalendar(anio, mes_num):
            for numero in semana:
                if not numero:
                    dias.append(None)
                    continue
                fecha = f'{anio}-{mes_num:02d}-{numero:02d}'
                reserva = por_fecha.get(fecha)
                dias.append({
                    'numero': numero, 'fecha': fecha,
                    'estado': reserva.estado if reserva else 'disponible',
                    'reserva': reserva,
                })
        meses.append({'nombre': MESES_ES[mes_num - 1], 'dias': dias})
    return meses
