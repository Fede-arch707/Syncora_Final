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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input-texto'
