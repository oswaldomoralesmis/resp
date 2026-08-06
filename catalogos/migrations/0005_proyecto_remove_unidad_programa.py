from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0004_fusionar_proyectos_duplicados'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='proyecto',
            unique_together={('ejercicio', 'dependencia', 'clave')},
        ),
        migrations.RemoveField(
            model_name='proyecto',
            name='unidad',
        ),
        migrations.RemoveField(
            model_name='proyecto',
            name='programa',
        ),
    ]
