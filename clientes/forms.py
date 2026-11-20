# clientes/forms.py
"""Formulario de la app clientes — W08."""
from django import forms

from .models import Cliente

def clean_correo(self):
        correo = self.cleaned_data['correo']
        clientes = Cliente.objects.filter(correo=correo)

        if self.instance.pk:
            clientes = clientes.exclude(pk=self.instance.pk)

        if clientes.exists():
            raise forms.ValidationError(
                'Este correo ya existe.'
            )

        return correo
class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes."""

    class Meta:
        model = Cliente
        fields = ['nombre', 'correo', 'telefono', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'erp-input',
                'placeholder': 'Nombre completo del cliente',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'erp-input',
                'placeholder': 'correo@ejemplo.com',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'erp-input',
                'placeholder': 'Teléfono de contacto',
            }),
            'activo': forms.CheckboxInput(),
        }
        labels = {
            'nombre': 'Nombre',
            'correo': 'Correo electrónico',
            'telefono': 'Teléfono',
            'activo': 'Activo',
        }
