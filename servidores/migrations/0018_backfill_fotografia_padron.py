# -*- coding: utf-8 -*-
from django.db import migrations


def backfill_fotografia(apps, schema_editor):
    """Para los registros de InformacionBasica que ya existían antes de que
    existiera la 'fotografía del periodo', no hay forma de saber cómo se
    veían los datos personales del servidor en ese momento exacto — se
    rellenan con el dato ACTUAL de Padrón como mejor aproximación disponible
    (puede no coincidir con exactitud si después se corrigió algo en Padrón).
    Los registros nuevos, de aquí en adelante, se llenan siempre desde la
    fila del layout en el momento de la carga (ver cargas/procesador.py)."""
    InformacionBasica = apps.get_model('servidores', 'InformacionBasica')
    ServidorPublico = apps.get_model('servidores', 'ServidorPublico')
    tabla_ib = InformacionBasica._meta.db_table
    tabla_sp = ServidorPublico._meta.db_table
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {tabla_ib} AS ib
            SET expediente = sp.expediente,
                rfc = sp.rfc,
                curp = sp.curp,
                determinante = sp.determinante,
                nombre = sp.nombre,
                primer_apellido = sp.primer_apellido,
                segundo_apellido = COALESCE(sp.segundo_apellido, ''),
                fecha_nacimiento = sp.fecha_nacimiento,
                sexo = sp.sexo,
                estado_civil_id = sp.estado_civil_id,
                entidad_nacimiento_id = sp.entidad_nacimiento_id,
                pais_nacimiento_id = sp.pais_nacimiento_id,
                correo_institucional = sp.correo_institucional,
                iss = sp.iss,
                nss = sp.nss,
                sindicato_id = sp.sindicato_id,
                sindicalizado = sp.sindicalizado,
                tiene_otra_plaza = sp.tiene_otra_plaza
            FROM {tabla_sp} AS sp
            WHERE ib.servidor_id = sp.id AND ib.nombre = ''
            """
        )


def revertir(apps, schema_editor):
    # No se deshace: son solo datos de respaldo, no información capturada
    # por una carga real. Dejarlos en blanco de nuevo no tiene beneficio y
    # sí el riesgo de perder la fotografía real de registros creados
    # después de aplicar esta migración pero antes de un rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('servidores', '0017_informacionbasica_fotografia_padron'),
    ]

    operations = [
        migrations.RunPython(backfill_fotografia, revertir),
    ]
