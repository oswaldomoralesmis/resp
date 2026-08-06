from django.db import migrations
from django.db.models import Count


def fusionar_duplicados(apps, schema_editor):
    """Antes, un Proyecto se repetía por cada unidad/programa (la combinación
    única incluía esos campos). Ahora que Proyecto.programas es M2M, esos
    duplicados (mismo ejercicio+dependencia+clave) deben fusionarse en un solo
    registro que junte todos sus programas, antes de poder aplicar la nueva
    restricción única ejercicio+dependencia+clave."""
    Proyecto = apps.get_model('catalogos', 'Proyecto')
    Puesto = apps.get_model('servidores', 'Puesto')
    InformacionBasica = apps.get_model('servidores', 'InformacionBasica')

    grupos = (
        Proyecto.objects.values('ejercicio', 'dependencia_id', 'clave')
        .annotate(n=Count('id'))
        .filter(n__gt=1)
    )
    for grupo in grupos:
        ids = list(
            Proyecto.objects.filter(
                ejercicio=grupo['ejercicio'],
                dependencia_id=grupo['dependencia_id'],
                clave=grupo['clave'],
            ).order_by('id').values_list('id', flat=True)
        )
        principal_id, duplicados_ids = ids[0], ids[1:]
        principal = Proyecto.objects.get(pk=principal_id)
        for dup_id in duplicados_ids:
            dup = Proyecto.objects.get(pk=dup_id)
            for programa_id in dup.programas.values_list('id', flat=True):
                principal.programas.add(programa_id)
            Puesto.objects.filter(proyecto_id=dup_id).update(proyecto_id=principal_id)
            InformacionBasica.objects.filter(proyecto_id=dup_id).update(proyecto_id=principal_id)
            dup.delete()


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0003_proyecto_programas'),
        ('servidores', '0005_puesto_programa'),
    ]

    operations = [
        migrations.RunPython(fusionar_duplicados, revertir),
    ]
