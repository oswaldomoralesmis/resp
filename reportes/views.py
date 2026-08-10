# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from servidores.models import ServidorPublico, InformacionBasica, BajaServidorPublico, Puesto
from catalogos.models import Dependencia
from usuarios.mixins import filtrar_por_dependencia
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


@login_required
def reporte_index(request):
    return render(request, 'reportes/index.html', {'titulo': 'Reportes y Estadísticas'})


@login_required
def reporte_padron(request):
    qs = filtrar_por_dependencia(
        ServidorPublico.objects.filter(activo=True).select_related('entidad_nacimiento', 'pais_nacimiento', 'sindicato'),
        request.user, 'informacion_basica__dependencia_id',
    ).distinct()
    dep = request.GET.get('dependencia', '')
    if dep:
        qs = qs.filter(informacion_basica__dependencia_id=dep, informacion_basica__activo=True)
    context = {
        'servidores': qs[:500],
        'total': qs.count(),
        'dependencias': filtrar_por_dependencia(Dependencia.objects.all(), request.user, 'pk'),
        'titulo': 'Padrón de Servidores Públicos',
    }
    return render(request, 'reportes/padron.html', context)


@login_required
def reporte_bajas(request):
    bajas = filtrar_por_dependencia(
        BajaServidorPublico.objects.select_related('servidor', 'dependencia', 'motivo_baja'), request.user
    ).order_by('-fecha_baja')
    return render(request, 'reportes/bajas.html', {'bajas': bajas, 'titulo': 'Bajas de Servidores Públicos'})


@login_required
def reporte_declaracion(request):
    registros = filtrar_por_dependencia(
        InformacionBasica.objects.filter(activo=True, oblig_declaracion='S')
        .select_related('servidor', 'dependencia', 'tipo_declaracion'),
        request.user,
    ).order_by('dependencia', 'servidor')
    return render(request, 'reportes/declaracion.html', {
        'registros': registros, 'titulo': 'Declaración Patrimonial - Sujetos Obligados'
    })


@login_required
def reporte_entrega_recepcion(request):
    registros = filtrar_por_dependencia(
        InformacionBasica.objects.filter(activo=True, oblig_entrega_recepcion='S').select_related('servidor', 'dependencia'),
        request.user,
    ).order_by('dependencia', 'servidor')
    return render(request, 'reportes/entrega_recepcion.html', {
        'registros': registros, 'titulo': 'Padrón - Acta de Entrega-Recepción'
    })


@login_required
def reporte_compatibilidad(request):
    servidores_doble = filtrar_por_dependencia(
        ServidorPublico.objects.filter(activo=True, tiene_otra_plaza='S'),
        request.user, 'informacion_basica__dependencia_id',
    ).distinct()
    return render(request, 'reportes/compatibilidad.html', {
        'servidores': servidores_doble, 'titulo': 'Compatibilidad de Horarios'
    })


@login_required
def reporte_estadisticas(request):
    info_visible = filtrar_por_dependencia(InformacionBasica.objects.filter(activo=True), request.user)
    puestos_visibles = filtrar_por_dependencia(Puesto.objects.all(), request.user, 'proyecto__dependencia')
    servidores_visibles = filtrar_por_dependencia(
        ServidorPublico.objects.filter(activo=True), request.user, 'informacion_basica__dependencia_id'
    ).distinct()
    bajas_visibles = filtrar_por_dependencia(BajaServidorPublico.objects.all(), request.user)

    ocupadas = list(info_visible.values('estatus_plaza__descripcion').annotate(total=Count('id')))
    vacantes = list(
        puestos_visibles.filter(servidor_actual__isnull=True).values('estatus_plaza__descripcion').annotate(total=Count('id'))
    )

    por_estatus_map = {}
    for item in ocupadas + vacantes:
        label = item['estatus_plaza__descripcion'] or 'Sin estatus'
        por_estatus_map[label] = por_estatus_map.get(label, 0) + item['total']

    stats = {
        'por_dependencia': info_visible.values(
            'dependencia__descripcion'
        ).annotate(total=Count('id')).order_by('-total')[:15],
        'por_estatus': [
            {'estatus_plaza__descripcion': label, 'total': total}
            for label, total in sorted(por_estatus_map.items(), key=lambda item: (-item[1], item[0]))
        ],
        'por_contratacion': info_visible.values(
            'nombramiento__descripcion'
        ).annotate(total=Count('id')),
        'total_activos': servidores_visibles.count(),
        'total_bajas': bajas_visibles.count(),
    }
    return render(request, 'reportes/estadisticas.html', {'stats': stats, 'titulo': 'Estadísticas Generales'})


@login_required
def exportar_excel(request, tipo):
    wb = openpyxl.Workbook()
    ws = wb.active
    header_fill = PatternFill(start_color='1B4F72', end_color='1B4F72', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    if tipo == 'padron':
        ws.title = 'Padrón RESP'
        headers = ['Expediente', 'RFC', 'CURP', 'Nombre', 'Primer Apellido', 'Segundo Apellido',
                   'Fecha Nacimiento', 'Sexo', 'Correo Institucional', 'ISS', 'NSS', 'Activo']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        servidores_export = filtrar_por_dependencia(
            ServidorPublico.objects.filter(activo=True), request.user, 'informacion_basica__dependencia_id'
        ).distinct()
        for row, s in enumerate(servidores_export, 2):
            ws.cell(row=row, column=1, value=s.expediente)
            ws.cell(row=row, column=2, value=s.rfc)
            ws.cell(row=row, column=3, value=s.curp)
            ws.cell(row=row, column=4, value=s.nombre)
            ws.cell(row=row, column=5, value=s.primer_apellido)
            ws.cell(row=row, column=6, value=s.segundo_apellido or '')
            ws.cell(row=row, column=7, value=str(s.fecha_nacimiento))
            ws.cell(row=row, column=8, value=s.sexo)
            ws.cell(row=row, column=9, value=s.correo_institucional)
            ws.cell(row=row, column=10, value=s.iss)
            ws.cell(row=row, column=11, value=s.nss)
            ws.cell(row=row, column=12, value='Sí' if s.activo else 'No')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="RESP_{tipo}.xlsx"'
    wb.save(response)
    return response


# Override reporte_index to include items
def reporte_index(request):
    from django.contrib.auth.decorators import login_required
    items = [
        {'icono': '📄', 'nombre': 'Padrón General', 'desc': 'Listado completo de servidores activos', 'url': '/reportes/padron/'},
        {'icono': '⚖️', 'nombre': 'Declaración Patrimonial', 'desc': 'Sujetos obligados a declarar', 'url': '/reportes/declaracion-patrimonial/'},
        {'icono': '🤝', 'nombre': 'Entrega-Recepción', 'desc': 'Padrón de actas de entrega-recepción', 'url': '/reportes/entrega-recepcion/'},
        {'icono': '🚫', 'nombre': 'Bajas', 'desc': 'Registro histórico de bajas', 'url': '/reportes/bajas/'},
        {'icono': '🔄', 'nombre': 'Compatibilidad', 'desc': 'Servidores con más de una plaza', 'url': '/reportes/compatibilidad-horarios/'},
        {'icono': '📈', 'nombre': 'Estadísticas', 'desc': 'Indicadores generales del RESP', 'url': '/reportes/estadisticas/'},
    ]
    return render(request, 'reportes/index.html', {'reporte_items': items, 'titulo': 'Reportes'})
