# -*- coding: utf-8 -*-
from django import forms
from .models import (
    FuenteFinanciamiento, Dependencia, UnidadAdministrativa,
    Programa, Proyecto, Categoria, TipoContratacion, TipoPersonal,
    TipoFuncion, NivelEstructura, EstatusPlaza, CentroTrabajo,
    TipoDeclaracion, Area, NivelEscolaridad, Discapacidad,
    EnfermedadCronica, Pueblo, MotivoBaja, Idioma, EstadoCivil,
    Pais, EntidadFederativa, Municipio, Sindicato, Inmueble,
)

FC  = 'form-control'
FS  = 'form-select'
FCU = 'form-control text-uppercase'


class FuenteFinanciamientoForm(forms.ModelForm):
    class Meta:
        model  = FuenteFinanciamiento
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 152801'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Descripción de la fuente'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class DependenciaForm(forms.ModelForm):
    class Meta:
        model  = Dependencia
        fields = ['ejercicio', 'clave', 'descripcion']
        widgets = {
            'ejercicio':   forms.NumberInput(attrs={'class': FC, 'placeholder': '2025'}),
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 21', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Nombre de la dependencia'}),
        }
        labels = {'ejercicio': 'Ejercicio', 'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class UnidadAdministrativaForm(forms.ModelForm):
    class Meta:
        model  = UnidadAdministrativa
        fields = ['ejercicio', 'dependencia', 'clave', 'descripcion']
        widgets = {
            'ejercicio':   forms.NumberInput(attrs={'class': FC, 'placeholder': '2025'}),
            'dependencia': forms.Select(attrs={'class': FS}),
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 21060301', 'maxlength': '10'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Nombre de la unidad administrativa'}),
        }
        labels = {
            'ejercicio':   'Ejercicio',
            'dependencia': 'Dependencia',
            'clave':       'Clave Unidad (8 dígitos)',
            'descripcion': 'Descripción',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class ProgramaForm(forms.ModelForm):
    class Meta:
        model  = Programa
        fields = ['ejercicio', 'dependencia', 'unidad', 'clave', 'descripcion']
        widgets = {
            'ejercicio':   forms.NumberInput(attrs={'class': FC, 'placeholder': '2025'}),
            'dependencia': forms.Select(attrs={'class': FS}),
            'unidad':      forms.Select(attrs={'class': FS}),
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: E054', 'maxlength': '10'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Descripción del programa'}),
        }
        labels = {
            'ejercicio':   'Ejercicio',
            'dependencia': 'Dependencia',
            'unidad':      'Unidad Administrativa',
            'clave':       'Clave Programa',
            'descripcion': 'Descripción',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class ProyectoForm(forms.ModelForm):
    class Meta:
        model  = Proyecto
        fields = ['ejercicio', 'dependencia', 'unidad', 'programa', 'clave', 'descripcion']
        widgets = {
            'ejercicio':   forms.NumberInput(attrs={'class': FC, 'placeholder': '2025'}),
            'dependencia': forms.Select(attrs={'class': FS}),
            'unidad':      forms.Select(attrs={'class': FS}),
            'programa':    forms.Select(attrs={'class': FS}),
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 04000127', 'maxlength': '20'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Descripción del proyecto'}),
        }
        labels = {
            'ejercicio':   'Ejercicio',
            'dependencia': 'Dependencia',
            'unidad':      'Unidad Administrativa',
            'programa':    'Programa',
            'clave':       'Clave Proyecto',
            'descripcion': 'Descripción',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class CategoriaForm(forms.ModelForm):
    class Meta:
        model  = Categoria
        fields = ['clave', 'subcategoria', 'descripcion', 'tipo_plaza', 'tp', 'nivel']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: CDI0603', 'maxlength': '15'}),
            'subcategoria':forms.NumberInput(attrs={'class': FC, 'placeholder': '0'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: SUBDIRECTOR'}),
            'tipo_plaza':  forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Confianza Estructura'}),
            'tp':          forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: CE', 'maxlength': '5'}),
            'nivel':       forms.NumberInput(attrs={'class': FC, 'placeholder': '0'}),
        }
        labels = {
            'clave':       'Clave',
            'subcategoria':'Subcategoría',
            'descripcion': 'Descripción',
            'tipo_plaza':  'Tipo de Plaza',
            'tp':          'TP',
            'nivel':       'Nivel',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()

    def clean_tp(self):
        return self.cleaned_data.get('tp', '').upper().strip()


class TipoContratacionForm(forms.ModelForm):
    class Meta:
        model  = TipoContratacion
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: C', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: CONFIANZA'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class TipoPersonalForm(forms.ModelForm):
    class Meta:
        model  = TipoPersonal
        fields = ['clave', 'tipo_contratacion', 'descripcion']
        widgets = {
            'clave':             forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: CE', 'maxlength': '5'}),
            'tipo_contratacion': forms.Select(attrs={'class': FS}),
            'descripcion':       forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: CONFIANZA ESTRUCTURA'}),
        }
        labels = {
            'clave':             'Clave',
            'tipo_contratacion': 'Tipo de Contratación',
            'descripcion':       'Descripción',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class TipoFuncionForm(forms.ModelForm):
    class Meta:
        model  = TipoFuncion
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: MM', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: MANDOS MEDIOS'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class NivelEstructuraForm(forms.ModelForm):
    class Meta:
        model  = NivelEstructura
        fields = ['clave', 'descripcion', 'nivel']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: CDI0603', 'maxlength': '15'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: SUBDIRECTOR'}),
            'nivel':       forms.NumberInput(attrs={'class': FC, 'placeholder': '0'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción', 'nivel': 'Nivel'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class EstatusPlazaForm(forms.ModelForm):
    class Meta:
        model  = EstatusPlaza
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: O', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Ocupada'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class CentroTrabajoForm(forms.ModelForm):
    class Meta:
        model  = CentroTrabajo
        fields = ['clave', 'nombre', 'nivel_educativo', 'municipio', 'domicilio']
        widgets = {
            'clave':           forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 27DJN0227S', 'maxlength': '20'}),
            'nombre':          forms.TextInput(attrs={'class': FC,  'placeholder': 'Nombre del centro de trabajo'}),
            'nivel_educativo': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: PREESCOLAR'}),
            'municipio':       forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: CENTRO'}),
            'domicilio':       forms.TextInput(attrs={'class': FC,  'placeholder': 'Calle, número, colonia'}),
        }
        labels = {
            'clave':           'Clave CCT',
            'nombre':          'Nombre del Centro',
            'nivel_educativo': 'Nivel Educativo',
            'municipio':       'Municipio',
            'domicilio':       'Domicilio',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class TipoDeclaracionForm(forms.ModelForm):
    class Meta:
        model  = TipoDeclaracion
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: C', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Completa'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class AreaForm(forms.ModelForm):
    class Meta:
        model  = Area
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: 1', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: REQUIRENTE'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}


class NivelEscolaridadForm(forms.ModelForm):
    class Meta:
        model  = NivelEscolaridad
        fields = ['clave', 'descripcion', 'estatus']
        widgets = {
            'clave':       forms.NumberInput(attrs={'class': FC, 'placeholder': '1'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Licenciatura'}),
            'estatus':     forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Terminado o Pasante'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción del Nivel', 'estatus': 'Estatus'}


class DiscapacidadForm(forms.ModelForm):
    class Meta:
        model  = Discapacidad
        fields = ['clave', 'tipo', 'descripcion']
        widgets = {
            'clave':       forms.NumberInput(attrs={'class': FC, 'placeholder': '0'}),
            'tipo':        forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: DISCAPACIDAD FISICA'}),
            'descripcion': forms.Textarea(attrs={'class': FC, 'rows': 3, 'placeholder': 'Descripción detallada'}),
        }
        labels = {'clave': 'Clave', 'tipo': 'Tipo de Discapacidad', 'descripcion': 'Descripción'}


class EnfermedadCronicaForm(forms.ModelForm):
    class Meta:
        model  = EnfermedadCronica
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.NumberInput(attrs={'class': FC, 'placeholder': '1'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Hipertensión'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}


class PuebloForm(forms.ModelForm):
    class Meta:
        model  = Pueblo
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.NumberInput(attrs={'class': FC, 'placeholder': '1'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Pueblo Chontal de Tabasco'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}


class MotivoBajaForm(forms.ModelForm):
    class Meta:
        model  = MotivoBaja
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: M', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Renuncia'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class IdiomaForm(forms.ModelForm):
    class Meta:
        model  = Idioma
        fields = ['clave', 'identificador_cndh', 'descripcion', 'familia_linguistica']
        widgets = {
            'clave':               forms.NumberInput(attrs={'class': FC, 'placeholder': '1'}),
            'identificador_cndh':  forms.NumberInput(attrs={'class': FC, 'placeholder': '101'}),
            'descripcion':         forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Náhuatl'}),
            'familia_linguistica': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Yuto-nahua'}),
        }
        labels = {
            'clave':               'Clave',
            'identificador_cndh':  'Identificador CNDH',
            'descripcion':         'Idioma / Lengua',
            'familia_linguistica': 'Familia Lingüística',
        }


class EstadoCivilForm(forms.ModelForm):
    class Meta:
        model  = EstadoCivil
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: CA', 'maxlength': '5'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Casado/a'}),
        }
        labels = {'clave': 'Clave', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class PaisForm(forms.ModelForm):
    class Meta:
        model  = Pais
        fields = ['clave', 'nombre']
        widgets = {
            'clave':  forms.NumberInput(attrs={'class': FC, 'placeholder': 'Ej: 700'}),
            'nombre': forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: ESTADOS UNIDOS MEXICANOS'}),
        }
        labels = {'clave': 'Clave', 'nombre': 'Nombre del País'}


class EntidadFederativaForm(forms.ModelForm):
    class Meta:
        model  = EntidadFederativa
        fields = ['clave', 'abreviatura', 'nombre']
        widgets = {
            'clave':       forms.NumberInput(attrs={'class': FC, 'placeholder': 'Ej: 27'}),
            'abreviatura': forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: TC', 'maxlength': '5'}),
            'nombre':      forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Tabasco'}),
        }
        labels = {'clave': 'Clave', 'abreviatura': 'Abreviatura', 'nombre': 'Nombre'}

    def clean_abreviatura(self):
        return self.cleaned_data.get('abreviatura', '').upper().strip()


class MunicipioForm(forms.ModelForm):
    class Meta:
        model  = Municipio
        fields = ['abreviatura', 'entidad', 'clave', 'nombre']
        widgets = {
            'abreviatura': forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: Tab.', 'maxlength': '10'}),
            'entidad':     forms.Select(attrs={'class': FS}),
            'clave':       forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: 004', 'maxlength': '5'}),
            'nombre':      forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Centro'}),
        }
        labels = {
            'abreviatura': 'Abreviatura',
            'entidad':     'Entidad Federativa',
            'clave':       'Clave',
            'nombre':      'Nombre del Municipio',
        }


class SindicatoForm(forms.ModelForm):
    class Meta:
        model  = Sindicato
        fields = ['clave', 'descripcion']
        widgets = {
            'clave':       forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: SUTSET', 'maxlength': '20'}),
            'descripcion': forms.TextInput(attrs={'class': FC,  'placeholder': 'Nombre completo del sindicato'}),
        }
        labels = {'clave': 'Clave / Siglas', 'descripcion': 'Descripción'}

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()


class InmuebleForm(forms.ModelForm):
    class Meta:
        model  = Inmueble
        fields = [
            'dependencia', 'clave', 'descripcion', 'calle',
            'estado', 'municipio', 'localidad', 'num_exterior',
            'num_interior', 'colonia', 'cp', 'telefono',
            'tipo_contrato', 'superficie_total', 'superficie_construida',
        ]
        widgets = {
            'dependencia':          forms.Select(attrs={'class': FS}),
            'clave':                forms.TextInput(attrs={'class': FCU, 'placeholder': 'Ej: IT001', 'maxlength': '10'}),
            'descripcion':          forms.TextInput(attrs={'class': FC,  'placeholder': 'Nombre del inmueble'}),
            'calle':                forms.TextInput(attrs={'class': FC,  'placeholder': 'Calle y número'}),
            'estado':               forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Tabasco'}),
            'municipio':            forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Centro'}),
            'localidad':            forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: Villahermosa'}),
            'num_exterior':         forms.TextInput(attrs={'class': FC,  'placeholder': 'Núm. exterior', 'maxlength': '10'}),
            'num_interior':         forms.TextInput(attrs={'class': FC,  'placeholder': 'Núm. interior', 'maxlength': '10'}),
            'colonia':              forms.TextInput(attrs={'class': FC,  'placeholder': 'Colonia o fraccionamiento'}),
            'cp':                   forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: 86035', 'maxlength': '10'}),
            'telefono':             forms.TextInput(attrs={'class': FC,  'placeholder': 'Ej: 9931234567'}),
            'tipo_contrato':        forms.Select(attrs={'class': FS}),
            'superficie_total':     forms.NumberInput(attrs={'class': FC, 'placeholder': '0.00', 'step': '0.01'}),
            'superficie_construida':forms.NumberInput(attrs={'class': FC, 'placeholder': '0.00', 'step': '0.01'}),
        }
        labels = {
            'dependencia':          'Dependencia',
            'clave':                'Clave',
            'descripcion':          'Descripción',
            'calle':                'Calle',
            'estado':               'Estado',
            'municipio':            'Municipio',
            'localidad':            'Localidad',
            'num_exterior':         'Núm. Exterior',
            'num_interior':         'Núm. Interior',
            'colonia':              'Colonia',
            'cp':                   'Código Postal',
            'telefono':             'Teléfono',
            'tipo_contrato':        'Tipo de Contrato',
            'superficie_total':     'Superficie Total (m²)',
            'superficie_construida':'Superficie Construida (m²)',
        }

    def clean_clave(self):
        return self.cleaned_data.get('clave', '').upper().strip()
