# -*- coding: utf-8 -*-
from django.db import models
from usuarios.models import UsuarioRESP
from catalogos.models import Dependencia


class PeriodoCarga(models.Model):
    quincena = models.CharField(max_length=7, unique=True, verbose_name='Quincena (AAAA-QQ)')
    fecha_inicio = models.DateField(verbose_name='Fecha inicio de carga')
    fecha_fin = models.DateField(verbose_name='Fecha fin de carga')
    activo = models.BooleanField(default=True, verbose_name='Período activo')

    class Meta:
        verbose_name = 'Período de Carga'
        verbose_name_plural = 'Períodos de Carga'
        ordering = ['-quincena']

    def __str__(self):
        return f"Quincena {self.quincena} ({self.fecha_inicio} - {self.fecha_fin})"


class CargaLayout(models.Model):
    TIPO_CHOICES = [
        ('basica', 'Información Básica'),
        ('personales', 'Datos Personales'),
        ('bajas', 'Bajas'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('con_errores', 'Con Errores'),
    ]
    periodo = models.ForeignKey(PeriodoCarga, on_delete=models.PROTECT, verbose_name='Período')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT, verbose_name='Dependencia')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Layout')
    archivo = models.FileField(upload_to='cargas/', verbose_name='Archivo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    registros_totales = models.IntegerField(default=0)
    registros_ok = models.IntegerField(default=0)
    registros_error = models.IntegerField(default=0)
    log_errores = models.TextField(blank=True)
    usuario_carga = models.ForeignKey(UsuarioRESP, on_delete=models.SET_NULL, null=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carga de Layout'
        verbose_name_plural = 'Cargas de Layouts'
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"{self.tipo} - {self.dependencia} - {self.periodo.quincena}"
