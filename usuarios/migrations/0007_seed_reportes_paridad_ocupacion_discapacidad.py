# -*- coding: utf-8 -*-
"""Siembra las 3 opciones de menú nuevas de Reportes (Paridad, Ocupación
de Plazas, Discapacidad), igual patrón que 0004_seed_opciones_permisos:
permitidas por defecto para todos los roles no-admin, para no quitarle
acceso a nadie de entrada."""
from django.db import migrations

OPCIONES = [
    # (clave, nombre, modulo, orden, permitido_por_defecto_no_admin)
    ('reporte_paridad', 'Monitor de Paridad', 'Reportes', 115, True),
    ('reporte_ocupacion', 'Ocupación de Plazas', 'Reportes', 116, True),
    ('reporte_discapacidad', 'Monitor de Discapacidad', 'Reportes', 117, True),
]

ROLES_NO_ADMIN = ['plantilla', 'validador', 'empleado', 'consulta', 'oic', 'general']


def sembrar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')

    for clave, nombre, modulo, orden, permitido in OPCIONES:
        opcion, _ = OpcionAplicativo.objects.get_or_create(
            clave=clave, defaults={'nombre': nombre, 'modulo': modulo, 'orden': orden},
        )
        for rol in ROLES_NO_ADMIN:
            RolPermiso.objects.get_or_create(
                rol=rol, opcion=opcion, defaults={'permitido': permitido},
            )


def revertir(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.filter(clave__in=[o[0] for o in OPCIONES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_seed_edicion_padron_infobasica_plazas'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
