# -*- coding: utf-8 -*-
"""Quita la opción de menú 'Validar Complementarios' sembrada en 0008: ese
botón manual se reemplazó por la validación automática al ACEPTAR la carga
de Datos Personales (ver cargas/views.py::_registrar_eventos_de_carga y
cargas/procesador.py::procesar_layout_personales) — ya no hace falta un
permiso de menú aparte para esto."""
from django.db import migrations

CLAVE = 'validar_complementarios'


def quitar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    OpcionAplicativo.objects.filter(clave=CLAVE).delete()


def restaurar(apps, schema_editor):
    OpcionAplicativo = apps.get_model('usuarios', 'OpcionAplicativo')
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')
    opcion, _ = OpcionAplicativo.objects.get_or_create(
        clave=CLAVE,
        defaults={'nombre': 'Validar Complementarios', 'modulo': 'Servidores Públicos', 'orden': 35},
    )
    RolPermiso.objects.get_or_create(rol='validador', opcion=opcion, defaults={'permitido': True})


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0008_seed_validar_complementarios'),
    ]

    operations = [
        migrations.RunPython(quitar, restaurar),
    ]
