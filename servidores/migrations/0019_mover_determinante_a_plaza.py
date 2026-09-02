# -*- coding: utf-8 -*-
from django.db import migrations, models


def backfill_determinante(apps, schema_editor):
    """El Determinante es propio de la PLAZA, no del servidor — un mismo
    servidor con más de una plaza puede tener un Determinante distinto en
    cada una, y el campo único en ServidorPublico no podía representar eso
    (se quedaba con el de la última fila procesada en cada carga). Como
    mejor aproximación disponible, se copia el Determinante que tenía cada
    servidor hacia TODAS las plazas que ocupa actualmente que aún no tengan
    uno propio — no es exacto si de verdad tenía Determinantes distintos por
    plaza, pero es lo único que había guardado hasta ahora."""
    ServidorPublico = apps.get_model('servidores', 'ServidorPublico')
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {apps.get_model('servidores', 'Puesto')._meta.db_table} AS p
            SET determinante = sp.determinante
            FROM {ServidorPublico._meta.db_table} AS sp
            WHERE p.servidor_actual_id = sp.id
              AND sp.determinante IS NOT NULL AND sp.determinante != ''
              AND (p.determinante IS NULL OR p.determinante = '')
            """
        )


def revertir(apps, schema_editor):
    # No se deshace: es solo un respaldo de mejor esfuerzo, no información
    # capturada por una carga real. Ver razones en 0018_backfill_fotografia_padron.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('servidores', '0018_backfill_fotografia_padron'),
    ]

    operations = [
        migrations.AddField(
            model_name='puesto',
            name='determinante',
            field=models.CharField(
                blank=True,
                help_text='Es propio de la plaza, no del servidor — un servidor con más de una '
                           'plaza puede tener un Determinante distinto en cada una.',
                max_length=20, verbose_name='Determinante',
            ),
        ),
        migrations.RunPython(backfill_determinante, revertir),
        migrations.RemoveField(
            model_name='servidorpublico',
            name='determinante',
        ),
    ]
