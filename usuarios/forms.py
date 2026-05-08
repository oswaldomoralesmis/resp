# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioRESP


class UsuarioRESPForm(UserCreationForm):

    class Meta:
        model  = UsuarioRESP
        fields = ['username', 'email', 'first_name', 'last_name',
                  'rfc', 'curp', 'rol', 'dependencia']
        widgets = {
            'username':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@tabasco.gob.mx'}),
            'first_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre(s)'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'rfc':         forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '13', 'placeholder': 'RFC con homoclave'}),
            'curp':        forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '18', 'placeholder': 'CURP 18 caracteres'}),
            'rol':         forms.Select(attrs={'class': 'form-select'}),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'username':    'Usuario (login)',
            'email':       'Correo institucional',
            'first_name':  'Nombre(s)',
            'last_name':   'Apellidos',
            'rfc':         'RFC',
            'curp':        'CURP',
            'rol':         'Rol en el sistema',
            'dependencia': 'Dependencia',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar form-control a los campos de contraseña que crea UserCreationForm
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})

    def clean_rfc(self):
        return self.cleaned_data.get('rfc', '').upper().strip()

    def clean_curp(self):
        return self.cleaned_data.get('curp', '').upper().strip()
