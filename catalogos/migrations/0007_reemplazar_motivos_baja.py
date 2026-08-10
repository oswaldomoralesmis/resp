from django.db import migrations

NUEVOS_MOTIVOS = [
    ('1', 'RENUNCIA'),
    ('2', 'JUBILACIÓN'),
    ('3', 'RETIRO DEL ENCARGO POR SANCIÓN.'),
    ('4', 'DEFUNCIÓN'),
    ('5', 'ABANDONO DE LABORES'),
    ('6', 'INCAPACIDAD TOTAL Y PERMANENTE'),
    ('7', 'INCUMPLIMIENTO DE OBLIGACIONES'),
    ('8', 'REPROBAR CAPACITACIÓN'),
    ('9', 'EVALUACIÓN DEL DESEMPEÑO DEFICIENTE'),
    ('10', 'SENTENCIA EJECUTORIA QUE IMPLIQUE PENA PRIVATIVA DE LA LIBERTAD'),
    ('11', 'INHABILITACIÓN'),
    ('12', 'DESTITUCIÓN E INHABILITACIÓN'),
    ('13', 'PUESTO SUPRIMIDO'),
    ('14', 'POR RESOLUCIÓN ADMINISTRATIVA QUE REVOQUE EL NOMBRAMIENTO'),
    ('15', 'POR NULIDAD DEL NOMBRAMIENTO'),
    ('16', 'ENLACE QUE NO ACREDITA SU PRIMERA EVALUACIÓN DEL DESEMPEÑO'),
    ('17', 'RETIRO VOLUNTARIO'),
    ('18', 'DESTITUCIÓN'),
    ('19', 'POR REPROBAR EVALUACIÓN DEL DESEMPEÑO'),
    ('20', 'POR REPROBAR CERTIFICACIÓN DE CAPACIDADES'),
    ('21', 'POR NO ACREDITAR EVALUACIÓN INDIVIDUAL (DEFICIENTE)'),
    ('22', 'POR INCAPACIDAD PARCIAL Y PERMANENTE'),
    ('23', 'POR RESOLUCIÓN ADMINISTRATIVA O JURISDICCIONAL QUE IMPIDA EL EJERCICIO DE LA PROFESIÓN'),
    ('24', 'PERMISO SIN GOCE DE SUELDO POR MAS DE 60 DÍAS'),
    ('25', 'SUSPENSION POR MAS DE 60 DIAS NATURALES SIN GOCE DE SUELDO'),
    ('26', 'TÉRMINO DE NOMBRAMIENTO'),
    ('27', 'CONCLUSIÓN DE CONTRATO'),
    ('28', 'PENSIÓN'),
    ('29', 'LIQUIDACIÓN'),
    ('30', 'CAMBIO DE UNIDAD RESPONSABLE DE LA PLAZA'),
    ('31', 'CAMBIO DE RAMO Y UNIDAD RESPONSABLE DE LA PLAZA'),
    ('32', 'NO APROBAR POR SEGUNDA OCASIÓN LA EVALUACIÓN DEL DESEMPEÑO'),
    ('33', 'LICENCIA SIN GOCE DE SUELDO'),
    ('34', 'INCAPACIDAD PERMANENTE'),
    ('35', 'OTRO'),
    ('36', 'RESCISIÓN DE CONTRATO'),
]


def reemplazar(apps, schema_editor):
    MotivoBaja = apps.get_model('catalogos', 'MotivoBaja')
    BajaServidorPublico = apps.get_model('servidores', 'BajaServidorPublico')
    # No se puede eliminar un MotivoBaja en uso (on_delete=PROTECT); se reasignan
    # las bajas existentes al nuevo motivo "OTRO" antes de limpiar el catálogo.
    otro, _ = MotivoBaja.objects.update_or_create(clave='TMP01', defaults={'descripcion': 'OTRO'})
    BajaServidorPublico.objects.exclude(motivo_baja=None).update(motivo_baja=otro)
    MotivoBaja.objects.exclude(pk=otro.pk).delete()
    otro.delete()
    for clave, descripcion in NUEVOS_MOTIVOS:
        MotivoBaja.objects.create(clave=clave, descripcion=descripcion)


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0006_alter_dependencia_unique_together_and_more'),
        ('servidores', '0010_alter_puesto_options_and_more'),
    ]

    operations = [
        migrations.RunPython(reemplazar, revertir),
    ]
