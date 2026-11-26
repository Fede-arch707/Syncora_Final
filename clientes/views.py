from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from .forms import ClienteForm, RegistroForm
from .models import Cliente


def registro(request):
    if request.user.is_authenticated:
        return redirect('calendario')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Cuenta creada correctamente.')
        return redirect('calendario')
    return render(request, 'registration/registro.html', {'form': form})


@login_required
def crear(request):
    form = ClienteForm(request.POST or None)
    reserva_form = None
    quiere_reservar = request.method == 'POST' and bool(request.POST.get('estado'))
    if quiere_reservar:
        from reservas.forms import ReservaRapidaForm
        reserva_form = ReservaRapidaForm(request.POST)

    if request.method == 'POST':
        cliente_valido = form.is_valid()
        reserva_valida = reserva_form.is_valid() if reserva_form is not None else True
        if reserva_form is not None and cliente_valido and form.cleaned_data['vetado']:
            reserva_form.add_error(None, 'Un cliente vetado no puede realizar reservas.')
            reserva_valida = False
        if cliente_valido and reserva_valida:
            with transaction.atomic():
                cliente = form.save()
                if reserva_form is not None:
                    reserva = reserva_form.save(commit=False)
                    reserva.cliente = cliente
                    reserva.full_clean()
                    reserva.save()
            messages.success(request, 'Cliente y reserva creados.' if reserva_form is not None else 'Cliente creado correctamente.')
            return redirect('calendario')

    return render(request, 'clientes/formulario.html', {
        'form': form, 'reserva_form': reserva_form,
        'titulo': 'Nuevo cliente', 'mostrar_reserva': reserva_form is not None,
    })


@login_required
def detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    reservas = cliente.reservas.select_related('salon', 'tipo_evento').order_by('-fecha')
    return render(request, 'clientes/detalle.html', {'cliente': cliente, 'reservas': reservas})


@login_required
def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('calendario')
    return render(request, 'clientes/formulario.html', {
        'form': form, 'titulo': 'Editar cliente', 'cliente': cliente,
    })


@login_required
def borrar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method != 'POST':
        return redirect('cliente_detalle', pk=pk)
    try:
        cliente.delete()
    except ProtectedError:
        messages.error(request, 'No se puede borrar el cliente porque tiene reservas registradas. Conservar el historial evita perder información.')
        return redirect('cliente_detalle', pk=pk)
    messages.success(request, 'Cliente eliminado.')
    return redirect('calendario')


@login_required
def exportar_excel(request):
    from .excel import MIME_XLSX, generar_excel
    respuesta = HttpResponse(generar_excel(), content_type=MIME_XLSX)
    nombre = f'Clientes_El_Poli_{timezone.localdate():%Y-%m-%d}.xlsx'
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    respuesta['Cache-Control'] = 'private, no-store'
    return respuesta
