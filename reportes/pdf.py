# -*- coding: utf-8 -*-
"""Exportación a PDF de los reportes de Paridad, Ocupación de Plazas y
Discapacidad — mismos estilos institucionales que cargas/comprobante.py
(colores, tipografías, tablas), con gráficas de pastel para los totales
y barras horizontales dentro de cada fila de las tablas cruzadas. A
diferencia de las pantallas HTML (que solo muestran el Top 15 para que
la tabla no crezca sin límite en pantalla), el PDF siempre recibe las
listas completas — la vista es responsable de llamar a las funciones de
stats con top=None antes de pasarlas aquí."""
import io

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend

AZUL_INSTITUCIONAL = colors.HexColor('#0b3d6b')
GRIS_CLARO = colors.HexColor('#f2f2f2')
MORADO = colors.HexColor('#7b1550')
DORADO = colors.HexColor('#c9a227')
VERDE = colors.HexColor('#1a6b4a')
GRIS_MEDIO = colors.HexColor('#999999')


def _estilos():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        name='TituloComprobante', parent=base['Title'],
        fontSize=16, textColor=AZUL_INSTITUCIONAL, alignment=TA_CENTER, spaceAfter=2,
    ))
    base.add(ParagraphStyle(
        name='Subtitulo', parent=base['Normal'],
        fontSize=9, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=14,
    ))
    base.add(ParagraphStyle(
        name='SeccionTitulo', parent=base['Heading2'],
        fontSize=12, textColor=AZUL_INSTITUCIONAL, spaceBefore=16, spaceAfter=6,
    ))
    return base


def _encabezado(story, estilos, titulo):
    story.append(Paragraph(titulo, estilos['TituloComprobante']))
    story.append(Paragraph(
        f'RESP Tabasco — generado el {timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")}',
        estilos['Subtitulo'],
    ))


def _titulo_seccion(story, estilos, texto):
    """Título de sección que siempre arranca en una página nueva — así cada
    sección del reporte (tabla o gráfica) queda completa de un vistazo, sin
    que el corte de página caiga a la mitad."""
    story.append(PageBreak())
    story.append(Paragraph(texto, estilos['SeccionTitulo']))


def _pie(datos, paleta, width=320, height=150):
    """'datos': lista de {'label', 'total', 'porcentaje'}. Filas con total=0
    se omiten (una porción de tamaño 0 rompe el layout del pastel)."""
    datos = [d for d in datos if d['total'] > 0] or [{'label': 'Sin datos', 'total': 1, 'porcentaje': 100}]
    d = Drawing(width, height)
    pie = Pie()
    pie.x, pie.y = 10, 10
    pie.width, pie.height = 130, 130
    pie.data = [item['total'] for item in datos]
    pie.labels = [f"{item['porcentaje']}%" for item in datos]
    pie.slices.strokeWidth = 0.75
    pie.slices.strokeColor = colors.white
    for i, _item in enumerate(datos):
        pie.slices[i].fillColor = paleta[i % len(paleta)]
    d.add(pie)
    leyenda = Legend()
    leyenda.x, leyenda.y = 160, 110
    leyenda.dx, leyenda.dy = 9, 9
    leyenda.fontSize = 9
    leyenda.alignment = 'right'
    leyenda.colorNamePairs = [
        (paleta[i % len(paleta)], f"{item['label']} ({item['total']:,})") for i, item in enumerate(datos)
    ]
    d.add(leyenda)
    return d


def _linea_evolucion(datos, width=460, height=200):
    """Línea de % Hombres / % Mujeres a lo largo del tiempo, estilo la
    gráfica de 'Evolución... por sexo' del RUSP federal. 'datos': lista
    ordenada cronológicamente de {'label', 'pct_hombres', 'pct_mujeres'}."""
    if not datos:
        d = Drawing(width, height)
        d.add(String(width / 2, height / 2, 'Sin datos históricos todavía.', fontSize=9, fillColor=colors.grey, textAnchor='middle'))
        return d

    d = Drawing(width, height)
    chart = HorizontalLineChart()
    chart.x = 45
    chart.y = 35
    chart.width = width - 70
    chart.height = height - 60
    chart.data = [
        [item['pct_hombres'] for item in datos],
        [item['pct_mujeres'] for item in datos],
    ]
    chart.categoryAxis.categoryNames = [item['label'] for item in datos]
    chart.categoryAxis.labels.angle = 60
    chart.categoryAxis.labels.dy = -8
    chart.categoryAxis.labels.fontSize = 5.5
    chart.categoryAxis.labels.boxAnchor = 'ne'
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labelTextFormat = '%d%%'
    chart.lines[0].strokeColor = DORADO
    chart.lines[0].strokeWidth = 1.6
    chart.lines[1].strokeColor = MORADO
    chart.lines[1].strokeWidth = 1.6
    chart.lineLabelFormat = None
    d.add(chart)

    leyenda = Legend()
    leyenda.x, leyenda.y = width - 10, height - 8
    leyenda.dx, leyenda.dy = 8, 8
    leyenda.fontSize = 8
    leyenda.alignment = 'right'
    leyenda.colorNamePairs = [(DORADO, 'Hombres'), (MORADO, 'Mujeres')]
    d.add(leyenda)
    return d


def _barra_horizontal(pct_a, pct_b, color_a, color_b, width=70, height=10):
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=colors.HexColor('#eeeeee'), strokeColor=None))
    ancho_a = width * (pct_a / 100.0)
    ancho_b = width * (pct_b / 100.0)
    if ancho_a > 0:
        d.add(Rect(0, 0, ancho_a, height, fillColor=color_a, strokeColor=None))
    if ancho_b > 0:
        d.add(Rect(ancho_a, 0, ancho_b, height, fillColor=color_b, strokeColor=None))
    return d


def _tabla_cruce_sexo(items, etiqueta_columna, estilo_celda):
    encabezado = [etiqueta_columna, 'Hombres', 'Mujeres', 'Total', '% Mujeres / Hombres']
    datos = [encabezado]
    for it in items:
        datos.append([
            Paragraph(str(it['label']), estilo_celda),
            f"{it['hombres']:,}", f"{it['mujeres']:,}", f"{it['total']:,}",
            _barra_horizontal(it['pct_mujeres'], it['pct_hombres'], MORADO, DORADO),
        ])
    tabla = Table(datos, colWidths=(6.5 * cm, 2 * cm, 2 * cm, 2 * cm, 3 * cm), hAlign='LEFT', repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tabla


def _tabla_cruce_ocupacion(items, etiqueta_columna, estilo_celda):
    encabezado = [etiqueta_columna, 'Ocupadas', 'Vacantes', 'Total', '% Ocupación']
    datos = [encabezado]
    for it in items:
        datos.append([
            Paragraph(str(it['label']), estilo_celda),
            f"{it['ocupadas']:,}", f"{it['vacantes']:,}", f"{it['total']:,}",
            _barra_horizontal(it['pct_ocupadas'], 100 - it['pct_ocupadas'], VERDE, colors.HexColor('#f3d9a0')),
        ])
    tabla = Table(datos, colWidths=(6.5 * cm, 2 * cm, 2 * cm, 2 * cm, 3 * cm), hAlign='LEFT', repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tabla


def generar_pdf_paridad(stats):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = _estilos()
    estilo_celda = ParagraphStyle(name='Celda', fontSize=8, leading=10)
    story = []
    _encabezado(story, estilos, 'Monitor de Paridad de Género')

    story.append(Paragraph(f"Total de servidores públicos activos: <b>{stats['total_personas']:,}</b>", estilos['Normal']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_pie(stats['por_sexo_personas'], [MORADO, DORADO, GRIS_MEDIO]))

    story.append(Paragraph(
        'Los cruces siguientes cuentan plazas ocupadas vigentes (Información Básica activa) — un servidor con más '
        'de una plaza puede contar más de una vez, igual que en el Monitor de Paridad de la APF.',
        estilos['Subtitulo'],
    ))

    _titulo_seccion(story, estilos, 'Por Tipo de Contratación')
    story.append(_tabla_cruce_sexo(stats['por_contratacion'], 'Contratación', estilo_celda))

    _titulo_seccion(story, estilos, f"Por Categoría ({len(stats['por_categoria'])})")
    story.append(_tabla_cruce_sexo(stats['por_categoria'], 'Categoría', estilo_celda))

    _titulo_seccion(story, estilos, f"Por Dependencia ({len(stats['por_dependencia'])})")
    story.append(_tabla_cruce_sexo(stats['por_dependencia'], 'Dependencia', estilo_celda))

    _titulo_seccion(story, estilos, 'Evolución Histórica por Género — Mensual')
    story.append(Paragraph(
        'Usa todo el histórico de Información Básica (vigente y ya reemplazada); si un servidor tuvo más de una '
        'quincena en el mismo mes, se cuenta una sola vez (la más reciente).',
        estilos['Subtitulo'],
    ))
    story.append(_linea_evolucion(stats['evolucion_mensual']))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_tabla_cruce_sexo(stats['evolucion_mensual'], 'Periodo', estilo_celda))

    _titulo_seccion(story, estilos, 'Evolución Histórica por Género — Anual')
    story.append(_linea_evolucion(stats['evolucion_anual']))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_tabla_cruce_sexo(stats['evolucion_anual'], 'Periodo', estilo_celda))

    doc.build(story)
    return buffer.getvalue()


def generar_pdf_ocupacion(stats):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = _estilos()
    estilo_celda = ParagraphStyle(name='Celda', fontSize=8, leading=10)
    story = []
    _encabezado(story, estilos, 'Ocupación de Plazas')

    story.append(Paragraph(f"Total de plazas: <b>{stats['total']:,}</b>", estilos['Normal']))
    story.append(Spacer(1, 0.3 * cm))
    datos_pie = [
        {'label': 'Ocupadas', 'total': stats['ocupadas'], 'porcentaje': stats['pct_ocupadas']},
        {'label': 'Vacantes', 'total': stats['vacantes'], 'porcentaje': stats['pct_vacantes']},
    ]
    story.append(_pie(datos_pie, [VERDE, DORADO]))

    _titulo_seccion(story, estilos, 'Por Tipo de Contratación')
    story.append(_tabla_cruce_ocupacion(stats['por_contratacion'], 'Contratación', estilo_celda))

    _titulo_seccion(story, estilos, f"Por Categoría ({len(stats['por_categoria'])})")
    story.append(_tabla_cruce_ocupacion(stats['por_categoria'], 'Categoría', estilo_celda))

    _titulo_seccion(story, estilos, f"Por Dependencia ({len(stats['por_dependencia'])})")
    story.append(_tabla_cruce_ocupacion(stats['por_dependencia'], 'Dependencia', estilo_celda))

    doc.build(story)
    return buffer.getvalue()


def generar_pdf_discapacidad(stats):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = _estilos()
    estilo_celda = ParagraphStyle(name='Celda', fontSize=8, leading=10)
    story = []
    _encabezado(story, estilos, 'Monitor de Discapacidad')

    story.append(Paragraph(
        f"Servidores activos: <b>{stats['total_personas']:,}</b> &nbsp;·&nbsp; "
        f"Con discapacidad registrada: <b>{stats['total_con_discapacidad']:,}</b> ({stats['porcentaje']}%)",
        estilos['Normal'],
    ))
    story.append(Spacer(1, 0.3 * cm))
    datos_pie = [
        {'label': 'Con discapacidad', 'total': stats['total_con_discapacidad'], 'porcentaje': stats['porcentaje']},
        {
            'label': 'Sin discapacidad',
            'total': max(stats['total_personas'] - stats['total_con_discapacidad'], 0),
            'porcentaje': round(100 - stats['porcentaje'], 1),
        },
    ]
    story.append(_pie(datos_pie, [DORADO, colors.HexColor('#cccccc')]))

    story.append(Paragraph(
        'Excluye "Ninguna" y "Sin respuesta" del catálogo de Discapacidad. Un servidor puede tener más de un '
        'tipo registrado, así que puede contar más de una vez en el cruce por tipo.',
        estilos['Subtitulo'],
    ))

    _titulo_seccion(story, estilos, 'Por Tipo de Discapacidad')
    story.append(_tabla_cruce_sexo(stats['por_tipo_sexo'], 'Tipo', estilo_celda))

    _titulo_seccion(story, estilos, 'Por Rango de Edad')
    story.append(_tabla_cruce_sexo(stats['por_rango_edad'], 'Edad', estilo_celda))

    _titulo_seccion(story, estilos, 'Por Tipo de Contratación')
    story.append(_tabla_cruce_sexo(stats['por_contratacion'], 'Contratación', estilo_celda))

    _titulo_seccion(story, estilos, 'Sueldo Neto Promedio por Género')
    filas_sueldo = [['Género', 'Sueldo Promedio']] + [
        [d['label'], f"${d['promedio']:,.2f}"] for d in stats['sueldo_por_sexo']
    ]
    tabla_sueldo = Table(filas_sueldo, colWidths=(6.5 * cm, 4 * cm), hAlign='LEFT')
    tabla_sueldo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_sueldo)

    doc.build(story)
    return buffer.getvalue()
