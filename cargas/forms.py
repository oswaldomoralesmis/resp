# -*- coding: utf-8 -*-
from django import forms
from .models import CargaLayout, PeriodoCarga, AccesoExcepcionCarga


class CargaLayoutForm(forms.ModelForm):
    """No incluye 'periodo': la carga siempre va contra el período activo,
    que la vista asigna automáticamente (ver carga_layout en views.py).
    No se permite elegirlo desde el formulario."""

    class Meta:
        model  = CargaLayout
        fields = ['dependencia', 'tipo', 'archivo']
        widgets = {
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'tipo':        forms.Select(attrs={'class': 'form-select'}),
            'archivo':     forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        }
        labels = {
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


class GenerarPeriodosForm(forms.Form):
    ejercicio = forms.IntegerField(
        label='Ejercicio', min_value=2000, max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2026', 'style': 'width:110px;'}),
    )


class PeriodoCargaForm(forms.ModelForm):

    class Meta:
        model  = PeriodoCarga
        fields = '__all__'
        widgets = {
            'quincena':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 01', 'maxlength': '2'}),
            'fecha_inicio':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'quincena':    'Número de Quincena (01-24)',
            'fecha_inicio':'Fecha inicio de quincena',
            'fecha_fin':   'Fecha fin de quincena',
            'activo':      'Período activo',
        }

    def clean_quincena(self):
        valor = self.cleaned_data.get('quincena', '').strip()
        if not valor.isdigit() or not (1 <= int(valor) <= 24):
            raise forms.ValidationError('La quincena debe ser un número del 01 al 24.')
        return valor.zfill(2)

    def clean(self):
        cleaned = super().clean()
        # 'ejercicio' no es un campo del formulario (se calcula de fecha_inicio
        # en el save() del modelo), así que Django no puede validar solo con
        # los campos del form la restricción única (ejercicio, quincena).
        # Se valida aquí a mano para no reventar con un IntegrityError.
        fecha_inicio = cleaned.get('fecha_inicio')
        quincena = cleaned.get('quincena')
        if fecha_inicio and quincena:
            existe = PeriodoCarga.objects.filter(ejercicio=fecha_inicio.year, quincena=quincena)
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                self.add_error(
                    'quincena',
                    f'Ya existe la quincena {quincena} para el ejercicio {fecha_inicio.year}.'
                )
        return cleaned


class AccesoExcepcionCargaForm(forms.ModelForm):

    class Meta:
        model  = AccesoExcepcionCarga
        fields = ['periodo', 'dependencia', 'fecha_inicio', 'fecha_fin', 'motivo']
        widgets = {
            'periodo':     forms.Select(attrs={'class': 'form-select'}),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motivo':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo de la excepción (opcional)'}),
        }
        labels = {
            'periodo':     'Período',
            'dependencia': 'Dependencia',
            'fecha_inicio':'Fecha inicio de acceso',
            'fecha_fin':   'Fecha fin de acceso',
            'motivo':      'Motivo',
        }

    def clean(self):
        cleaned = super().clean()
        ini = cleaned.get('fecha_inicio')
        fin = cleaned.get('fecha_fin')
        if ini and fin and fin < ini:
            raise forms.ValidationError('La fecha fin de acceso no puede ser anterior a la fecha inicio.')
        return cleaned
