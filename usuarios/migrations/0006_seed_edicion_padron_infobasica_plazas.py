# -*- coding: utf-8 -*-
"""Habilita el permiso de edición configurable para Padrón, Inf. Básica
Quincenal y Plazas, y siembra 'puede_editar' con el mismo valor que ya
tenía 'permitido' para esas tres — hoy quien puede VER esas secciones
también puede editarlas sin restricción, así que activar este cambio no le
quita a nadie una capacidad que ya tenía hasta que un administrador entre
a la pantalla de permisos y desmarque algo."""
from django.db import migrations

CLAVES_CON_EDICION = ['padron', 'info_basica', 'plazas']


def sembrar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')

    OpcionAplicativo.objects.filter(clave__in=CLAVES_CON_EDICION).update(tiene_edicion=True)

    for permiso in RolPermiso.objects.filter(opcion__clave__in=CLAVES_CON_EDICION):
        if permiso.permitido and not permiso.puede_editar:
            permiso.puede_editar = True
            permiso.save(update_fields=['puede_editar'])


def revertir(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')
    RolPermiso.objects.filter(opcion__clave__in=CLAVES_CON_EDICION).update(puede_editar=False)
    OpcionAplicativo.objects.filter(clave__in=CLAVES_CON_EDICION).update(tiene_edicion=False)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_opcionaplicativo_tiene_edicion_and_more'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
