import datetime

from django.db import migrations


def sumar_dias_habiles(fecha, dias):
    actual = fecha
    contados = 0
    while contados < dias:
        actual += datetime.timedelta(days=1)
        if actual.weekday() < 5:  # 0=lunes ... 4=viernes
            contados += 1
    return actual


def recalcular_con_3_dias(apps, schema_editor):
    """La ventana de carga pasó de 5 a 3 días hábiles después del fin de
    quincena; recalcula fecha_cierre de los períodos ya creados."""
    PeriodoCarga = apps.get_model('cargas', 'PeriodoCarga')
    for periodo in PeriodoCarga.objects.all():
        periodo.fecha_cierre = sumar_dias_habiles(periodo.fecha_fin, 3)
        periodo.save(update_fields=['fecha_cierre'])


def recalcular_con_5_dias(apps, schema_editor):
    PeriodoCarga = apps.get_model('cargas', 'PeriodoCarga')
    for periodo in PeriodoCarga.objects.all():
        periodo.fecha_cierre = sumar_dias_habiles(periodo.fecha_fin, 5)
        periodo.save(update_fields=['fecha_cierre'])


class Migration(migrations.Migration):

    dependencies = [
        ('cargas', '0005_periodocarga_ejercicio'),
    ]

    operations = [
        migrations.RunPython(recalcular_con_3_dias, recalcular_con_5_dias),
    ]
