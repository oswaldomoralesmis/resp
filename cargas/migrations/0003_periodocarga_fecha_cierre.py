import datetime

from django.db import migrations, models


def calcular_fecha_cierre(apps, schema_editor):
    PeriodoCarga = apps.get_model('cargas', 'PeriodoCarga')
    for periodo in PeriodoCarga.objects.all():
        actual = periodo.fecha_fin
        contados = 0
        while contados < 5:
            actual += datetime.timedelta(days=1)
            if actual.weekday() < 5:
                contados += 1
        periodo.fecha_cierre = actual
        periodo.save(update_fields=['fecha_cierre'])


def revertir_fecha_cierre(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cargas', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodocarga',
            name='fecha_cierre',
            field=models.DateField(editable=False, null=True, verbose_name='Fecha de cierre',
                                    help_text='Calculada automáticamente: 5 días hábiles después de la fecha fin.'),
        ),
        migrations.RunPython(calcular_fecha_cierre, revertir_fecha_cierre),
        migrations.AlterField(
            model_name='periodocarga',
            name='fecha_cierre',
            field=models.DateField(editable=False, verbose_name='Fecha de cierre',
                                    help_text='Calculada automáticamente: 5 días hábiles después de la fecha fin.'),
        ),
    ]
