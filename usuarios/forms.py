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


class RegistroForm(UserCreationForm):
    """Auto-registro público: a propósito NO incluye 'rol' ni 'dependencia'
    — eso lo asigna un administrador al activar la cuenta (ver
    usuarios.views.registro / activar_usuario). La cuenta queda inactiva
    hasta entonces."""

    class Meta:
        model  = UsuarioRESP
        fields = ['username', 'email', 'first_name', 'last_name', 'rfc', 'curp']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@tabasco.gob.mx'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre(s)'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'rfc':        forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '13', 'placeholder': 'RFC con homoclave'}),
            'curp':       forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '18', 'placeholder': 'CURP 18 caracteres'}),
        }
        labels = {
            'username':   'Usuario (login)',
            'email':      'Correo institucional',
            'first_name': 'Nombre(s)',
            'last_name':  'Apellidos',
            'rfc':        'RFC',
            'curp':       'CURP',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # is_active=True es el default del modelo (AbstractUser) en una
        # instancia nueva sin guardar; hay que fijarlo en False YA (no hasta
        # save()), porque UsuarioRESP.clean() —que exige dependencia para
        # roles no-administrador— corre durante is_valid(), antes de save(),
        # y de lo contrario rechaza el registro por "falta dependencia".
        self.instance.is_active = False
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})

    def clean_rfc(self):
        return self.cleaned_data.get('rfc', '').upper().strip()

    def clean_curp(self):
        return self.cleaned_data.get('curp', '').upper().strip()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_active = False
        usuario.activo_sistema = False
        if commit:
            usuario.save()
        return usuario


class ActivarUsuarioForm(forms.ModelForm):
    """El administrador asigna rol y dependencia al activar a un usuario
    (recién auto-registrado, o reactivando a uno dado de baja antes)."""

    class Meta:
        model  = UsuarioRESP
        fields = ['rol', 'dependencia']
        widgets = {
            'rol':         forms.Select(attrs={'class': 'form-select'}),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'rol': 'Rol en el sistema', 'dependencia': 'Dependencia'}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('rol') != 'administrador' and not cleaned.get('dependencia'):
            self.add_error('dependencia', 'La dependencia es obligatoria para usuarios que no son administradores.')
        return cleaned


class UsuarioRESPEditForm(forms.ModelForm):
    """Para editar un usuario existente: sin campos de contraseña y sin el
    clean_username de UserCreationForm, que no excluye la instancia actual
    y por eso siempre reportaba 'el usuario ya existe' al editar."""

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

    def clean_rfc(self):
        return self.cleaned_data.get('rfc', '').upper().strip()

    def clean_curp(self):
        return self.cleaned_data.get('curp', '').upper().strip()
