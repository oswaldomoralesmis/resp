# -*- coding: utf-8 -*-
"""Siembra la opción de menú del nuevo Censo Nacional de Gobierno (INEGI),
mismo patrón que 0007_seed_reportes_paridad_ocupacion_discapacidad: permitida
por defecto para todos los roles no-admin, para no quitarle acceso a nadie
de entrada."""
from django.db import migrations

CLAVE = 'reporte_censo_inegi'
NOMBRE = 'Censo Nacional de Gobierno (INEGI)'
MODULO = 'Reportes'
ORDEN = 118

ROLES_NO_ADMIN = ['plantilla', 'validador', 'empleado', 'consulta', 'oic', 'general']


def sembrar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')

    opcion, _ = OpcionAplicativo.objects.get_or_create(
        clave=CLAVE, defaults={'nombre': NOMBRE, 'modulo': MODULO, 'orden': ORDEN},
    )
    for rol in ROLES_NO_ADMIN:
        RolPermiso.objects.get_or_create(rol=rol, opcion=opcion, defaults={'permitido': True})


def revertir(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.filter(clave=CLAVE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0009_quitar_validar_complementarios'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
