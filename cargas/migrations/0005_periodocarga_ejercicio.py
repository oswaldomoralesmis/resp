from django.db import migrations, models


def poblar_ejercicio_y_normalizar_quincena(apps, schema_editor):
    """Antes 'quincena' guardaba 'AAAA-QQ' (con el año como prefijo). Ahora el
    año vive en el campo 'ejercicio' y 'quincena' es solo el número (01-24)."""
    PeriodoCarga = apps.get_model('cargas', 'PeriodoCarga')
    for periodo in PeriodoCarga.objects.all():
        periodo.ejercicio = periodo.fecha_inicio.year
        numero = periodo.quincena.rsplit('-', 1)[-1]
        numero = ''.join(ch for ch in numero if ch.isdigit()) or '00'
        periodo.quincena = numero.zfill(2)[:2]
        periodo.save()


def revertir(apps, schema_editor):
    PeriodoCarga = apps.get_model('cargas', 'PeriodoCarga')
    for periodo in PeriodoCarga.objects.all():
        periodo.quincena = f'{periodo.ejercicio}-{periodo.quincena}'
        periodo.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cargas', '0004_accesoexcepcioncarga'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodocarga',
            name='ejercicio',
            field=models.IntegerField(editable=False, null=True, verbose_name='Ejercicio'),
        ),
        migrations.RunPython(poblar_ejercicio_y_normalizar_quincena, revertir),
        migrations.AlterField(
            model_name='periodocarga',
            name='ejercicio',
            field=models.IntegerField(editable=False, verbose_name='Ejercicio'),
        ),
        migrations.AlterField(
            model_name='periodocarga',
            name='quincena',
            field=models.CharField(max_length=2, verbose_name='Quincena'),
        ),
        migrations.AlterUniqueTogether(
            name='periodocarga',
            unique_together={('ejercicio', 'quincena')},
        ),
        migrations.AlterModelOptions(
            name='periodocarga',
            options={'ordering': ['-fecha_inicio'], 'verbose_name': 'Período de Carga', 'verbose_name_plural': 'Períodos de Carga'},
        ),
    ]
