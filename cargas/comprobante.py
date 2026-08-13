# -*- coding: utf-8 -*-
"""Comprobante de carga en PDF: resumen imprimible de una CargaLayout, con
sus contadores y — si los hay — el detalle de los registros con error."""
import io

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

AZUL_INSTITUCIONAL = colors.HexColor('#0b3d6b')
GRIS_CLARO = colors.HexColor('#f2f2f2')
ROJO = colors.HexColor('#b71c1c')

ESTADO_LABELS = {
    'procesando':          'Procesando',
    'con_errores':         'Con errores de formato',
    'pendiente_revision':  'Pendiente de revisión',
    'aceptado':            'Aceptado',
    'rechazado':           'Rechazado',
    'pendiente':           'Pendiente',
}


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


def _tabla_datos(filas, col_widths=(5 * cm, 11 * cm)):
    t = Table(filas, colWidths=col_widths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), AZUL_INSTITUCIONAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
    ]))
    return t


def generar_comprobante_pdf(carga):
    """Devuelve los bytes del PDF de comprobante para 'carga'."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = _estilos()
    story = []

    story.append(Paragraph('Comprobante de Carga de Layout', estilos['TituloComprobante']))
    story.append(Paragraph(
        'Registro Estatal de Servidores Públicos — Gobierno del Estado de Tabasco',
        estilos['Subtitulo'],
    ))

    story.append(Paragraph('Datos de la carga', estilos['SeccionTitulo']))
    story.append(_tabla_datos([
        ['Folio', f'#{carga.pk}'],
        ['Tipo de layout', carga.get_tipo_display()],
        ['Período', f'Quincena {carga.periodo.quincena}/{carga.periodo.ejercicio} '
                     f'({carga.periodo.fecha_inicio:%d/%m/%Y} – {carga.periodo.fecha_fin:%d/%m/%Y})'],
        ['Dependencia', f'{carga.dependencia.clave} — {carga.dependencia.descripcion}'],
        ['Cargado por', str(carga.usuario_carga) if carga.usuario_carga else '—'],
        ['Fecha de carga', timezone.localtime(carga.fecha_carga).strftime('%d/%m/%Y %H:%M')],
        ['Estado actual', ESTADO_LABELS.get(carga.estado, carga.estado)],
    ]))

    story.append(Paragraph('Resultado del procesamiento', estilos['SeccionTitulo']))
    resumen = Table([
        ['Total de registros', 'Correctos', 'Con error / omitidos'],
        [str(carga.registros_totales), str(carga.registros_ok), str(carga.registros_error)],
    ], colWidths=(5.3 * cm, 5.3 * cm, 5.4 * cm), hAlign='LEFT')
    resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_INSTITUCIONAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2, 1), (2, 1), ROJO if carga.registros_error else colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(resumen)

    if carga.estado in ('aceptado', 'rechazado'):
        story.append(Paragraph('Revisión', estilos['SeccionTitulo']))
        filas_rev = [
            ['Decisión', ESTADO_LABELS.get(carga.estado, carga.estado)],
            ['Revisado por', str(carga.revisado_por) if carga.revisado_por else '—'],
            ['Fecha de revisión',
             timezone.localtime(carga.fecha_revision).strftime('%d/%m/%Y %H:%M') if carga.fecha_revision else '—'],
        ]
        if carga.estado == 'rechazado':
            filas_rev.append(['Motivo de rechazo', carga.motivo_rechazo or '—'])
        story.append(_tabla_datos(filas_rev))

    # ── Decisiones del validador sobre filas con error (trazabilidad) ────
    if carga.decisiones_filas:
        story.append(Paragraph(
            f'Revisión de registros con error ({len(carga.decisiones_filas)})', estilos['SeccionTitulo'],
        ))
        estilo_celda_dec = ParagraphStyle(name='CeldaDecision', fontSize=8, leading=10)
        filas_por_num = {f.get('fila'): f for f in (carga.detalle_filas or [])}
        datos_dec = [['Fila', 'RFC', 'Decisión', 'Motivo', 'Por', 'Fecha']]
        for num_str, d in sorted(carga.decisiones_filas.items(), key=lambda kv: int(kv[0])):
            f = filas_por_num.get(int(num_str), {})
            fecha_dec = d.get('fecha', '')
            parsed = parse_datetime(fecha_dec) if fecha_dec else None
            if parsed:
                fecha_dec = timezone.localtime(parsed).strftime('%d/%m/%Y %H:%M')
            datos_dec.append([
                num_str,
                f.get('rfc') or '—',
                'ACEPTADA' if d.get('decision') == 'aceptada' else 'RECHAZADA',
                Paragraph(d.get('motivo') or '—', estilo_celda_dec),
                Paragraph((d.get('por') or '—').strip(), estilo_celda_dec),
                fecha_dec,
            ])
        tabla_dec = Table(
            datos_dec, colWidths=(1.1 * cm, 2.6 * cm, 2 * cm, 5 * cm, 3.3 * cm, 2.5 * cm),
            hAlign='LEFT', repeatRows=1,
        )
        tabla_dec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tabla_dec)
        story.append(Spacer(1, 0.3 * cm))

    # ── Detalle de registros con error/omitidos ──────────────────────────
    filas_error = [f for f in (carga.detalle_filas or []) if f.get('estado') in ('ERROR', 'OMITIDA')]
    if filas_error:
        story.append(Paragraph(
            f'Registros con error u omitidos ({len(filas_error)})', estilos['SeccionTitulo'],
        ))
        estilo_celda = ParagraphStyle(name='Celda', fontSize=8, leading=10)
        datos = [['Fila', 'RFC', 'Nombre', 'Estado', 'Motivo']]
        for f in filas_error:
            datos.append([
                str(f.get('fila', '')),
                f.get('rfc') or '—',
                Paragraph(f.get('nombre') or '—', estilo_celda),
                f.get('estado', ''),
                Paragraph(f.get('mensaje') or '', estilo_celda),
            ])
        tabla_err = Table(
            datos, colWidths=(1.3 * cm, 3 * cm, 4 * cm, 2.2 * cm, 5.5 * cm),
            hAlign='LEFT', repeatRows=1,
        )
        tabla_err.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (3, 1), (3, -1), ROJO),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tabla_err)
    elif carga.detalle_filas:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            'Sin registros con error — todos los registros del archivo fueron procesados correctamente.',
            estilos['Normal'],
        ))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f'Comprobante generado el {timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")}. '
        f'Este comprobante refleja el estado de la carga al momento de generarse.',
        ParagraphStyle(name='Pie', fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)
    return buffer.getvalue()
