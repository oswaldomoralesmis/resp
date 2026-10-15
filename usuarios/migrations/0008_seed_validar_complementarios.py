# -*- coding: utf-8 -*-
"""Siembra la opción de menú 'Validar Datos Complementarios' (escolaridad y
pueblo indígena): a diferencia de 0004/0006/0007 (donde todos los roles
no-admin arrancan igual), aquí solo 'validador' queda con acceso de entrada
—es quien revisa esos datos del padrón, igual que ya revisa cargas de
layout, ver puede_revisar_carga en usuarios/mixins.py—. El resto de los
roles no-admin se deja SIN fila de RolPermiso a propósito: 'sin fila = sin
permiso' (ver usuario_tiene_permiso)."""
from django.db import migrations

CLAVE, NOMBRE, MODULO, ORDEN = 'validar_complementarios', 'Validar Complementarios', 'Servidores Públicos', 35
ROL_PERMITIDO = 'validador'


def sembrar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')
    opcion, _ = OpcionAplicativo.objects.get_or_create(
        clave=CLAVE, defaults={'nombre': NOMBRE, 'modulo': MODULO, 'orden': ORDEN},
    )
    RolPermiso.objects.get_or_create(rol=ROL_PERMITIDO, opcion=opcion, defaults={'permitido': True})


def revertir(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.filter(clave=CLAVE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_seed_reportes_paridad_ocupacion_discapacidad'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
