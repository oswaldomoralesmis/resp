# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from servidores.models import ServidorPublico, InformacionBasica, BajaServidorPublico
from catalogos.models import Dependencia
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


@login_required
def reporte_index(request):
    return render(request, 'reportes/index.html', {'titulo': 'Reportes y Estadísticas'})


@login_required
def reporte_padron(request):
    qs = ServidorPublico.objects.filter(activo=True).select_related(
        'entidad_nacimiento', 'pais_nacimiento', 'sindicato'
    )
    dep = request.GET.get('dependencia', '')
    if dep:
        qs = qs.filter(informacion_basica__dependencia_id=dep, informacion_basica__activo=True)
    context = {
        'servidores': qs[:500],
        'total': qs.count(),
        'dependencias': Dependencia.objects.all(),
        'titulo': 'Padrón de Servidores Públicos',
    }
    return render(request, 'reportes/padron.html', context)


@login_required
def reporte_bajas(request):
    bajas = BajaServidorPublico.objects.select_related(
        'servidor', 'dependencia', 'motivo_baja'
    ).order_by('-fecha_baja')
    return render(request, 'reportes/bajas.html', {'bajas': bajas, 'titulo': 'Bajas de Servidores Públicos'})


@login_required
def reporte_declaracion(request):
    registros = InformacionBasica.objects.filter(
        activo=True, oblig_declaracion='S'
    ).select_related('servidor', 'dependencia', 'tipo_declaracion').order_by('dependencia', 'servidor')
    return render(request, 'reportes/declaracion.html', {
        'registros': registros, 'titulo': 'Declaración Patrimonial - Sujetos Obligados'
    })


@login_required
def reporte_entrega_recepcion(request):
    registros = InformacionBasica.objects.filter(
        activo=True, oblig_entrega_recepcion='S'
    ).select_related('servidor', 'dependencia').order_by('dependencia', 'servidor')
    return render(request, 'reportes/entrega_recepcion.html', {
        'registros': registros, 'titulo': 'Padrón - Acta de Entrega-Recepción'
    })


@login_required
def reporte_compatibilidad(request):
    servidores_doble = ServidorPublico.objects.filter(
        activo=True, tiene_otra_plaza='S'
    ).select_related()
    return render(request, 'reportes/compatibilidad.html', {
        'servidores': servidores_doble, 'titulo': 'Compatibilidad de Horarios'
    })


@login_required
def reporte_estadisticas(request):
    stats = {
        'por_dependencia': InformacionBasica.objects.filter(activo=True).values(
            'dependencia__descripcion'
        ).annotate(total=Count('id')).order_by('-total')[:15],
        'por_estatus': InformacionBasica.objects.filter(activo=True).values(
            'estatus_plaza__descripcion'
        ).annotate(total=Count('id')),
        'por_contratacion': InformacionBasica.objects.filter(activo=True).values(
            'nombramiento__descripcion'
        ).annotate(total=Count('id')),
        'total_activos': ServidorPublico.objects.filter(activo=True).count(),
        'total_bajas': BajaServidorPublico.objects.count(),
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
        for row, s in enumerate(ServidorPublico.objects.filter(activo=True), 2):
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
