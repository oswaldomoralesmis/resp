# -*- coding: utf-8 -*-
import calendar
import datetime

from django.db import models
from usuarios.models import UsuarioRESP
from catalogos.models import Dependencia

DIAS_HABILES_CIERRE = 3


def sumar_dias_habiles(fecha, dias):
    """Suma 'dias' días hábiles (lunes a viernes) a 'fecha'. No considera días festivos."""
    actual = fecha
    contados = 0
    while contados < dias:
        actual += datetime.timedelta(days=1)
        if actual.weekday() < 5:  # 0=lunes ... 4=viernes
            contados += 1
    return actual


class PeriodoCarga(models.Model):
    ejercicio = models.IntegerField(editable=False, verbose_name='Ejercicio')
    quincena = models.CharField(max_length=2, verbose_name='Quincena')
    fecha_inicio = models.DateField(verbose_name='Fecha inicio de carga')
    fecha_fin = models.DateField(verbose_name='Fecha fin de carga')
    fecha_cierre = models.DateField(
        editable=False, verbose_name='Fecha de cierre',
        help_text=f'Calculada automáticamente: {DIAS_HABILES_CIERRE} días hábiles después de la fecha fin.'
    )
    activo = models.BooleanField(default=True, verbose_name='Período activo')

    class Meta:
        verbose_name = 'Período de Carga'
        verbose_name_plural = 'Períodos de Carga'
        unique_together = ['ejercicio', 'quincena']
        ordering = ['-fecha_inicio']

    def save(self, *args, **kwargs):
        self.ejercicio = self.fecha_inicio.year
        self.fecha_cierre = sumar_dias_habiles(self.fecha_fin, DIAS_HABILES_CIERRE)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Quincena {self.quincena}/{self.ejercicio} ({self.fecha_inicio} - {self.fecha_fin})"


def generar_periodos_ejercicio(ejercicio):
    """Crea los 24 períodos quincenales de 'ejercicio' (1-15 y 16-fin de mes
    de cada uno de los 12 meses), sin duplicar los que ya existan. La
    'quincena' de cada uno es solo su número (01-24); lo que la distingue
    entre ejercicios es el campo 'ejercicio', no un prefijo de año en el texto.
    Devuelve (creados, existentes)."""
    creados = existentes = 0
    num_quincena = 0
    for mes in range(1, 13):
        ultimo_dia = calendar.monthrange(ejercicio, mes)[1]
        for dia_inicio, dia_fin in [(1, 15), (16, ultimo_dia)]:
            num_quincena += 1
            quincena = f'{num_quincena:02d}'
            _, creado = PeriodoCarga.objects.get_or_create(
                ejercicio=ejercicio, quincena=quincena,
                defaults={
                    'fecha_inicio': datetime.date(ejercicio, mes, dia_inicio),
                    'fecha_fin': datetime.date(ejercicio, mes, dia_fin),
                },
            )
            if creado:
                creados += 1
            else:
                existentes += 1
    return creados, existentes


class AccesoExcepcionCarga(models.Model):
    """Ventana de fechas propia que el administrador otorga a una dependencia
    para cargar layouts de un período fuera de la ventana general
    (fecha_inicio-fecha_cierre) del período."""
    periodo = models.ForeignKey(PeriodoCarga, on_delete=models.CASCADE, related_name='excepciones', verbose_name='Período')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE, verbose_name='Dependencia')
    fecha_inicio = models.DateField(verbose_name='Fecha inicio de acceso')
    fecha_fin = models.DateField(verbose_name='Fecha fin de acceso')
    motivo = models.CharField(max_length=255, blank=True, verbose_name='Motivo')
    autorizado_por = models.ForeignKey(UsuarioRESP, on_delete=models.SET_NULL, null=True, verbose_name='Autorizado por')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Excepción de Acceso'
        verbose_name_plural = 'Excepciones de Acceso'
        unique_together = ['periodo', 'dependencia']
        ordering = ['-periodo', 'dependencia']

    def __str__(self):
        return f"{self.dependencia} - Quincena {self.periodo.quincena}/{self.periodo.ejercicio} ({self.fecha_inicio} a {self.fecha_fin})"


def ventana_permitida(periodo, dependencia):
    """Ventana de fechas (inicio, fin) en la que 'dependencia' puede cargar
    layouts de 'periodo': la excepción vigente para esa dependencia si existe,
    o si no la ventana general del período (fecha_fin - fecha_cierre; la carga
    se hace una vez cerrada la quincena, no durante fecha_inicio-fecha_fin)."""
    excepcion = periodo.excepciones.filter(dependencia=dependencia).first()
    if excepcion:
        return excepcion.fecha_inicio, excepcion.fecha_fin
    return periodo.fecha_fin, periodo.fecha_cierre


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
        return f"{self.tipo} - {self.dependencia} - Quincena {self.periodo.quincena}/{self.periodo.ejercicio}"
