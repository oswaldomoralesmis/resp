# -*- coding: utf-8 -*-
from django import forms
from .models import ServidorPublico, InformacionBasica, BajaServidorPublico, Puesto
from catalogos.models import Dependencia
from catalogos.forms import UnidadSelect


class ProgramaSelect(forms.Select):
    """<select> de Programa con data-unidad por opción, para que el JS del
    formulario de Puesto solo muestre los programas de la unidad elegida."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, 'instance', None)
        if instance is not None:
            option['attrs']['data-unidad'] = instance.unidad_id
        return option


class ProyectoSelect(forms.Select):
    """<select> de Proyecto con data-dependencia por opción, para que el JS del
    formulario de Puesto solo muestre los proyectos de la dependencia elegida."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, 'instance', None)
        if instance is not None:
            option['attrs']['data-dependencia'] = instance.dependencia_id
        return option


class ServidorPublicoForm(forms.ModelForm):

    class Meta:
        model  = ServidorPublico
        exclude = ['activo', 'fecha_creacion', 'fecha_actualizacion']
        widgets = {
            'expediente':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 41471'}),
            'rfc':                 forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '13', 'placeholder': 'Ej: GOCI7509233A6'}),
            'curp':                forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '18', 'placeholder': 'Ej: GOCI750923HTCNRS04'}),
            'determinante':        forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Determinante'}),
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
            'determinante':        'Determinante',
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


class PuestoForm(forms.ModelForm):
    dependencia = forms.ModelChoiceField(
        queryset=Dependencia.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Dependencia',
    )

    class Meta:
        model  = Puesto
        fields = [
            'proyecto', 'programa', 'unidad', 'id_plaza', 'categoria',
            'nombramiento', 'nivel_estructura', 'estatus_plaza', 'cct',
            'hsm', 'total_percepciones', 'total_bonos', 'total_neto', 'dias_pagados',
            'servidor_actual', 'id_plaza_jefe',
        ]
        widgets = {
            'proyecto':           ProyectoSelect(attrs={'class': 'form-select'}),
            'programa':           ProgramaSelect(attrs={'class': 'form-select'}),
            'unidad':             UnidadSelect(attrs={'class': 'form-select'}),
            'id_plaza':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 50694'}),
            'categoria':          forms.Select(attrs={'class': 'form-select'}),
            'nombramiento':       forms.Select(attrs={'class': 'form-select'}),
            'nivel_estructura':   forms.Select(attrs={'class': 'form-select'}),
            'estatus_plaza':      forms.Select(attrs={'class': 'form-select'}),
            'cct':                forms.Select(attrs={'class': 'form-select'}),
            'hsm':                forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_percepciones': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_bonos':        forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_neto':         forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'dias_pagados':       forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '15'}),
            'servidor_actual':    forms.Select(attrs={'class': 'form-select'}),
            'id_plaza_jefe':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID de plaza del jefe inmediato'}),
        }
        labels = {
            'proyecto':           'Proyecto',
            'programa':           'Programa',
            'unidad':             'Unidad Administrativa',
            'id_plaza':           'ID de Plaza',
            'categoria':          'Categoría',
            'nombramiento':       'Tipo de Contratación',
            'nivel_estructura':   'Nivel de Estructura',
            'estatus_plaza':      'Estatus de Plaza',
            'cct':                'Centro de Trabajo',
            'hsm':                'HSM (Hora-Semana-Mes)',
            'total_percepciones': 'Total Percepciones',
            'total_bonos':        'Total Bonos',
            'total_neto':         'Total Neto',
            'dias_pagados':       'Días Pagados',
            'servidor_actual':    'Trabajador Asignado',
            'id_plaza_jefe':      'ID Plaza Jefe Inmediato',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['id_plaza'].disabled = True
            self.fields['id_plaza'].widget.attrs['class'] += ' bg-light'
            if self.instance.proyecto_id:
                self.fields['dependencia'].initial = self.instance.proyecto.dependencia_id
