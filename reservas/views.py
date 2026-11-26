from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from clientes.forms import ClienteForm
from clientes.models import Cliente
from .calendario import generar_calendario
from .forms import PagoForm, ReservaForm
from .models import Reserva, Salon


@login_required
def calendario(request):
    try:
        anio = int(request.GET.get('anio', timezone.localdate().year))
        if not 2000 <= anio <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        anio = timezone.localdate().year
    salones = Salon.objects.filter(activo=True)
    salon = salones.filter(pk=request.GET.get('salon', '')).first() if str(request.GET.get('salon', '')).isdigit() else None
    if salon is None:
        salon = salones.first()
    reservas = (Reserva.objects.filter(salon=salon, fecha__year=anio)
                .select_related('cliente', 'salon').prefetch_related('pagos')) if salon else Reserva.objects.none()
    clientes = Cliente.objects.prefetch_related('reservas').order_by('nombre')
    filas_tabla = []
    for cliente in clientes:
        historial = sorted(cliente.reservas.all(), key=lambda r: r.fecha, reverse=True)
        ultima = historial[0] if historial else None
        filas_tabla.append({'cliente': cliente, 'ultima': ultima})
    return render(request, 'reservas/calendario.html', {
        'anio': anio, 'anio_anterior': anio - 1, 'anio_siguiente': anio + 1,
        'salones': salones, 'salon': salon, 'calendario_anual': generar_calendario(anio, reservas),
        'filas_tabla': filas_tabla, 'cliente_form': ClienteForm(),
    })


@login_required
def crear(request):
    initial = {}
    if request.method == 'GET':
        if request.GET.get('fecha'):
            initial['fecha'] = request.GET['fecha']
        if str(request.GET.get('salon', '')).isdigit():
            initial['salon'] = request.GET['salon']
        if str(request.GET.get('cliente', '')).isdigit():
            initial['cliente'] = request.GET['cliente']
    form = ReservaForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reserva creada.')
        return redirect('calendario')
    return render(request, 'reservas/formulario.html', {'form': form, 'titulo': 'Nueva reserva'})


@login_required
def detalle(request, pk):
    reserva = get_object_or_404(Reserva.objects.select_related('cliente', 'salon', 'tipo_evento').prefetch_related('pagos'), pk=pk)
    return render(request, 'reservas/detalle.html', {'reserva': reserva, 'pago_form': PagoForm()})


@login_required
def editar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    form = ReservaForm(request.POST or None, instance=reserva)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reserva actualizada.')
        return redirect('reserva_detalle', pk=pk)
    return render(request, 'reservas/formulario.html', {'form': form, 'titulo': 'Editar reserva', 'reserva': reserva})


@login_required
def borrar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method != 'POST':
        return redirect('reserva_detalle', pk=pk)
    reserva.delete()
    messages.success(request, 'Reserva eliminada.')
    return redirect('calendario')


@login_required
def agregar_pago(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method != 'POST':
        return redirect('reserva_detalle', pk=pk)
    with transaction.atomic():
        reserva = get_object_or_404(Reserva.objects.select_for_update(), pk=pk)
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.reserva = reserva
            if pago.monto > reserva.saldo:
                form.add_error('monto', 'El pago supera el saldo pendiente.')
            else:
                pago.full_clean()
                pago.save()
                messages.success(request, 'Pago registrado.')
                return redirect('reserva_detalle', pk=pk)
    reserva = Reserva.objects.select_related('cliente', 'salon', 'tipo_evento').prefetch_related('pagos').get(pk=pk)
    return render(request, 'reservas/detalle.html', {'reserva': reserva, 'pago_form': form}, status=400)
