# -*- coding: utf-8 -*-
from django import forms
from .models import ServidorPublico, InformacionBasica, BajaServidorPublico
from catalogos.models import Dependencia


class ServidorPublicoForm(forms.ModelForm):

    class Meta:
        model  = ServidorPublico
        exclude = ['activo', 'fecha_creacion', 'fecha_actualizacion']
        widgets = {
            'expediente':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 41471'}),
            'rfc':                 forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '13', 'placeholder': 'Ej: GOCI7509233A6'}),
            'curp':                forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '18', 'placeholder': 'Ej: GOCI750923HTCNRS04'}),
            'nombre':              forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Nombre(s)'}),
            'primer_apellido':     forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Apellido paterno'}),
            'segundo_apellido':    forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Apellido materno'}),
            'fecha_nacimiento':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexo':                forms.Select(attrs={'class': 'form-select'}),
            'estado_civil':        forms.Select(attrs={'class': 'form-select'}),
            'entidad_nacimiento':  forms.Select(attrs={'class': 'form-select'}),
            'pais_nacimiento':     forms.Select(attrs={'class': 'form-select'}),
            'correo_institucional':forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@tabasco.gob.mx'}),
            'iss':                 forms.Select(attrs={'class': 'form-select'}),
            'nss':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de seguridad social'}),
            'sindicalizado':       forms.Select(attrs={'class': 'form-select'}),
            'sindicato':           forms.Select(attrs={'class': 'form-select'}),
            'tiene_otra_plaza':    forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'expediente':          'No. Expediente',
            'rfc':                 'RFC',
            'curp':                'CURP',
            'nombre':              'Nombre(s)',
            'primer_apellido':     'Primer Apellido',
            'segundo_apellido':    'Segundo Apellido',
            'fecha_nacimiento':    'Fecha de Nacimiento',
            'sexo':                'Sexo',
            'estado_civil':        'Estado Civil',
            'entidad_nacimiento':  'Entidad de Nacimiento',
            'pais_nacimiento':     'País de Nacimiento',
            'correo_institucional':'Correo Institucional',
            'iss':                 'Instituto de Seguridad Social',
            'nss':                 'Núm. Seguridad Social',
            'sindicalizado':       '¿Sindicalizado?',
            'sindicato':           'Sindicato',
            'tiene_otra_plaza':    '¿Tiene otra plaza?',
        }

    def clean_rfc(self):
        return self.cleaned_data.get('rfc', '').upper().strip()

    def clean_curp(self):
        return self.cleaned_data.get('curp', '').upper().strip()

    def clean_nombre(self):
        return self.cleaned_data.get('nombre', '').upper().strip()

    def clean_primer_apellido(self):
        return self.cleaned_data.get('primer_apellido', '').upper().strip()

    def clean_segundo_apellido(self):
        v = self.cleaned_data.get('segundo_apellido', '')
        return v.upper().strip() if v else v


class InformacionBasicaForm(forms.ModelForm):

    class Meta:
        model  = InformacionBasica
        exclude = ['fecha_carga', 'activo']
        widgets = {
            'quincena':                    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-QQ  Ej: 2025-01'}),
            'fuente_financiamiento':       forms.Select(attrs={'class': 'form-select'}),
            'dependencia':                 forms.Select(attrs={'class': 'form-select'}),
            'unidad':                      forms.Select(attrs={'class': 'form-select'}),
            'programa':                    forms.Select(attrs={'class': 'form-select'}),
            'proyecto':                    forms.Select(attrs={'class': 'form-select'}),
            'id_plaza':                    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 50694'}),
            'categoria':                   forms.Select(attrs={'class': 'form-select'}),
            'puesto':                      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clave del puesto'}),
            'nombramiento':                forms.Select(attrs={'class': 'form-select'}),
            'nivel_estructura':            forms.Select(attrs={'class': 'form-select'}),
            'id_plaza_jefe':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID plaza del jefe inmediato'}),
            'puesto_jefe':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clave puesto del jefe'}),
            'hsm':                         forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_percepciones':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_bonos':                 forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_neto':                  forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'dias_pagados':                forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '15'}),
            'estatus_plaza':               forms.Select(attrs={'class': 'form-select'}),
            'servidor':                    forms.Select(attrs={'class': 'form-select'}),
            'cct':                         forms.Select(attrs={'class': 'form-select'}),
            'oblig_declaracion':           forms.Select(attrs={'class': 'form-select'}),
            'tipo_declaracion':            forms.Select(attrs={'class': 'form-select'}),
            'oblig_entrega_recepcion':     forms.Select(attrs={'class': 'form-select'}),
            'oblig_rendir_cuentas':        forms.Select(attrs={'class': 'form-select'}),
            'puesto_sensible':             forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso_gobierno':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_ingreso_dependencia':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_ingreso_puesto':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'area':                        forms.Select(attrs={'class': 'form-select'}),
            'participa_contrataciones':    forms.Select(attrs={'class': 'form-select'}),
            'nivel_contrataciones':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A / B / C'}),
            'participa_concesiones':       forms.Select(attrs={'class': 'form-select'}),
            'nivel_concesiones':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A / B / C'}),
            'participa_enajenacion':       forms.Select(attrs={'class': 'form-select'}),
            'nivel_enajenacion':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A / B / C'}),
            'participa_avaluos':           forms.Select(attrs={'class': 'form-select'}),
            'nivel_avaluos':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A / B / C'}),
            'inmueble':                    forms.Select(attrs={'class': 'form-select'}),
            'serc':                        forms.Select(attrs={'class': 'form-select'}),
            'exigibilidad_serc':           forms.Select(attrs={'class': 'form-select'}),
        }


class BajaForm(forms.ModelForm):

    class Meta:
        model  = BajaServidorPublico
        fields = ['dependencia', 'fecha_baja', 'motivo_baja', 'ejercicio', 'periodo']
        widgets = {
            'dependencia':  forms.Select(attrs={'class': 'form-select'}),
            'fecha_baja':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motivo_baja':  forms.Select(attrs={'class': 'form-select'}),
            'ejercicio':    forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2025'}),
            'periodo':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-QQ  Ej: 2025-01'}),
        }
        labels = {
            'dependencia':  'Dependencia',
            'fecha_baja':   'Fecha de Baja',
            'motivo_baja':  'Motivo de Baja',
            'ejercicio':    'Ejercicio',
            'periodo':      'Período (Quincena)',
        }
