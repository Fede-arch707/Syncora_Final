from django import forms
from django.forms import ModelForm
from .models import Reserva, Pago, Salon


class ReservaForm(ModelForm):
    class Meta:
        model = Reserva
        fields = ('cliente', 'salon', 'fecha', 'tipo_evento', 'estado', 'total', 'cuotas_totales', 'pagado_inicial', 'notas')
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'pagado_inicial': 'Pago inicial ($)', 'cuotas_totales': 'Cantidad de cuotas'}
        error_messages = {
            'cliente': {'required': 'Seleccioná el cliente que va a reservar.', 'invalid_choice': 'Elegí un cliente válido.'},
            'salon': {'required': 'Seleccioná el salón para la reserva.', 'invalid_choice': 'Elegí un salón disponible.'},
            'fecha': {'required': 'Seleccioná la fecha de la reserva.', 'invalid': 'Ingresá una fecha válida.'},
            'total': {'required': 'Ingresá el importe total.', 'invalid': 'Ingresá un importe válido, por ejemplo 100000.'},
            'cuotas_totales': {'required': 'Ingresá la cantidad de cuotas.', 'invalid': 'Ingresá un número de cuotas válido.'},
            'pagado_inicial': {'invalid': 'Ingresá un pago inicial válido, por ejemplo 20000.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input-texto'
        self.fields['salon'].queryset = Salon.objects.filter(activo=True) | Salon.objects.filter(pk=self.instance.salon_id) if self.instance.pk else Salon.objects.filter(activo=True)


class ReservaRapidaForm(ReservaForm):
    class Meta(ReservaForm.Meta):
        fields = ('salon', 'fecha', 'tipo_evento', 'estado', 'total', 'cuotas_totales', 'pagado_inicial', 'notas')


class PagoForm(ModelForm):
    class Meta:
        model = Pago
        fields = ('fecha', 'monto', 'metodo', 'nota')
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}
        error_messages = {
            'fecha': {'required': 'Indicá la fecha del pago.', 'invalid': 'Ingresá una fecha válida para el pago.'},
            'monto': {'required': 'Ingresá el monto del pago.', 'invalid': 'Ingresá un monto válido, por ejemplo 5000.'},
            'metodo': {'required': 'Seleccioná el método de pago.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input-texto'
