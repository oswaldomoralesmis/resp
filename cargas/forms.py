# -*- coding: utf-8 -*-
from django import forms
from .models import CargaLayout, PeriodoCarga


class CargaLayoutForm(forms.ModelForm):

    class Meta:
        model  = CargaLayout
        fields = ['periodo', 'dependencia', 'tipo', 'archivo']
        widgets = {
            'periodo':     forms.Select(attrs={'class': 'form-select'}),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'tipo':        forms.Select(attrs={'class': 'form-select'}),
            'archivo':     forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        }
        labels = {
            'periodo':     'Período (Quincena)',
            'dependencia': 'Dependencia',
            'tipo':        'Tipo de Layout',
            'archivo':     'Archivo Excel',
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            nombre = archivo.name.lower()
            if not (nombre.endswith('.xlsx') or nombre.endswith('.xls')):
                raise forms.ValidationError('Solo se permiten archivos Excel (.xlsx o .xls).')
            if archivo.size > 20 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar 20 MB.')
        return archivo


class PeriodoCargaForm(forms.ModelForm):

    class Meta:
        model  = PeriodoCarga
        fields = '__all__'
        widgets = {
            'quincena':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-QQ  Ej: 2025-01'}),
            'fecha_inicio':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'quincena':    'Clave de Quincena',
            'fecha_inicio':'Fecha inicio de recepción',
            'fecha_fin':   'Fecha fin de recepción',
            'activo':      'Período activo',
        }
