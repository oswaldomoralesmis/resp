import django.db.models.deletion
from django.db import migrations, models


def poblar_programa(apps, schema_editor):
    Puesto = apps.get_model('servidores', 'Puesto')
    for puesto in Puesto.objects.select_related('proyecto').all():
        if puesto.proyecto.programa_id:
            puesto.programa_id = puesto.proyecto.programa_id
            puesto.save(update_fields=['programa'])


def revertir_programa(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('servidores', '0004_alter_puesto_unique_together_alter_puesto_id_plaza'),
        ('catalogos', '0003_proyecto_programas'),
    ]

    operations = [
        migrations.AddField(
            model_name='puesto',
            name='programa',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='puestos', to='catalogos.programa', verbose_name='Programa',
            ),
        ),
        migrations.RunPython(poblar_programa, revertir_programa),
        migrations.AlterField(
            model_name='puesto',
            name='programa',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='puestos', to='catalogos.programa', verbose_name='Programa',
            ),
        ),
    ]
