# -*- coding: utf-8 -*-
"""Siembra la opción de permiso 'Ver Todas las Dependencias': hasta ahora
esa facultad (ver Padrón/Plazas/Cargas/Reportes sin quedar limitado a la
dependencia propia) solo la tenía el rol administrador, fija en código. Se
agrega aquí como una OpcionAplicativo más para que sea configurable desde
Permisos por Rol (p.ej. para dársela al rol General) — a propósito SIN
ninguna fila de RolPermiso: sin fila = sin permiso, así no se le otorga a
nadie de entrada; el administrador la activa a mano para el rol que
corresponda."""
from django.db import migrations

CLAVE = 'ver_todas_dependencias'
NOMBRE = 'Ver Todas las Dependencias (sin restricción)'
MODULO = 'Administración'
ORDEN = 135


def sembrar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.get_or_create(
        clave=CLAVE, defaults={'nombre': NOMBRE, 'modulo': MODULO, 'orden': ORDEN},
    )


def revertir(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.filter(clave=CLAVE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0010_seed_reporte_censo_inegi'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
