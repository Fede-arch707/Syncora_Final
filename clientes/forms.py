from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ('nombre', 'dni', 'telefono', 'direccion', 'observaciones', 'vetado')
        widgets = {'observaciones': forms.Textarea(attrs={'rows': 3})}
        error_messages = {
            'nombre': {'required': 'Escribí el nombre y apellido del cliente.'},
            'dni': {
                'required': 'Ingresá el DNI del cliente.',
                'unique': 'Este DNI ya está registrado. Buscá la ficha del cliente y creá la nueva reserva desde allí.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'input-texto'

    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if Cliente.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'Este DNI ya está registrado. Buscá la ficha del cliente y creá la nueva reserva desde allí.'
            )
        return dni


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Correo electrónico')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input-texto'
