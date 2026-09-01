# -*- coding: utf-8 -*-
"""Siembra el catálogo de opciones de menú y los permisos por rol de
arranque — deliberadamente iguales al comportamiento que ya existía en el
código (ver mixins.py/urls.py antes de este cambio), para que activar este
módulo no le quite ni le dé acceso a nadie hasta que un administrador
entre a la nueva pantalla y ajuste algo."""
from django.db import migrations

OPCIONES = [
    # (clave, nombre, modulo, orden, permitido_por_defecto_no_admin)
    ('padron', 'Padrón', 'Servidores Públicos', 10, True),
    ('info_basica', 'Inf. Básica Quincenal', 'Servidores Públicos', 20, True),
    ('plazas', 'Plazas', 'Servidores Públicos', 30, True),
    ('calendario_cargas', 'Calendario (Cargar Layout)', 'Carga de Información', 40, True),
    ('historial_cargas', 'Historial Cargas', 'Carga de Información', 50, True),
    ('reporte_padron', 'Padrón General', 'Reportes', 60, True),
    ('reporte_declaracion', 'Declaración Patrimonial', 'Reportes', 70, True),
    ('reporte_entrega_recepcion', 'Entrega-Recepción', 'Reportes', 80, True),
    ('reporte_bajas', 'Bajas', 'Reportes', 90, True),
    ('reporte_compatibilidad', 'Compatibilidad', 'Reportes', 100, True),
    ('reporte_estadisticas', 'Estadísticas', 'Reportes', 110, True),
    ('catalogos', 'Catálogos', 'Administración', 120, True),
    ('periodos_carga', 'Períodos de Carga', 'Administración', 130, True),
    ('usuarios', 'Usuarios', 'Administración', 140, False),
    ('excepciones_acceso', 'Excepciones de Acceso', 'Administración', 150, False),
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
        ('usuarios', '0003_opcionaplicativo_rolpermiso'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
