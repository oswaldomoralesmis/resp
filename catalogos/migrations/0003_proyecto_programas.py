from django.db import migrations, models


def poblar_programas(apps, schema_editor):
    Proyecto = apps.get_model('catalogos', 'Proyecto')
    for proyecto in Proyecto.objects.all():
        if proyecto.programa_id:
            proyecto.programas.add(proyecto.programa_id)


def revertir_programas(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0002_alter_programa_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='proyecto',
            name='programas',
            field=models.ManyToManyField(related_name='proyectos', to='catalogos.programa', verbose_name='Programas'),
        ),
        migrations.RunPython(poblar_programas, revertir_programas),
    ]
