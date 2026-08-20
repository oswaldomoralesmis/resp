# -*- coding: utf-8 -*-
import calendar
import datetime
import threading

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction, connection
from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone

from django.http import HttpResponse

from .models import (
    CargaLayout, PeriodoCarga, AccesoExcepcionCarga, ventana_permitida,
    generar_periodos_ejercicio, tipos_permitidos_periodo, periodo_vigente_hoy,
)
from .forms import CargaLayoutForm, PeriodoCargaForm, AccesoExcepcionCargaForm, GenerarPeriodosForm
from .procesador import procesar_layout_basica, procesar_layout_bajas
from .comprobante import generar_comprobante_pdf
from usuarios.mixins import (
    AdministradorRequiredMixin, DependenciaScopedMixin, filtrar_por_dependencia,
    admin_requerido, puede_revisar_carga,
)


def _correr_procesador(carga, dry_run, overrides):
    """Llama al procesador correspondiente al tipo de carga. Común a validar
    (dry_run=True) y aceptar (dry_run=False, con overrides)."""
    if carga.tipo == 'basica':
        return procesar_layout_basica(carga, dry_run=dry_run, overrides=overrides)
    elif carga.tipo == 'bajas':
        return procesar_layout_bajas(carga, dry_run=dry_run, overrides=overrides)
    return {'ok': 0, 'errores': 0, 'total': 0,
            'log': f'Tipo "{carga.tipo}" aún no implementado.', 'filas': []}


def _procesar_carga_en_segundo_plano(carga_pk, dry_run, overrides=None, revisado_por_pk=None):
    """Corre procesar_layout_* fuera del ciclo request/response, en un hilo
    aparte: subir o aceptar un archivo grande de layout puede tardar más de
    lo que nginx/gunicorn esperan una respuesta (504 Gateway Timeout). La
    vista que llama a esto ya dejó carga.estado='procesando' guardado antes
    de lanzar el hilo, así que la pantalla de detalle puede mostrar "en
    proceso" y auto-refrescarse (ver carga_detalle.html) hasta que este hilo
    actualice el registro con el resultado final.

    Cada hilo obtiene su propia conexión a la BD (Django la maneja por hilo
    automáticamente); se cierra explícitamente al terminar porque, a
    diferencia de una request normal, aquí no hay una señal de Django que
    la cierre sola."""
    try:
        carga = CargaLayout.objects.get(pk=carga_pk)
        try:
            if dry_run:
                resultado = _correr_procesador(carga, dry_run=True, overrides=overrides)
                carga.registros_totales = resultado['total']
                carga.registros_ok = resultado['ok']
                carga.registros_error = resultado['errores']
                carga.log_errores = resultado['log']
                carga.detalle_filas = resultado['filas']
                carga.estado = 'pendiente_revision'
                carga.save()
            else:
                with transaction.atomic():
                    resultado = _correr_procesador(carga, dry_run=False, overrides=overrides)
                    carga.registros_totales = resultado['total']
                    carga.registros_ok = resultado['ok']
                    carga.registros_error = resultado['errores']
                    carga.log_errores = resultado['log']
                    carga.detalle_filas = resultado['filas']
                    carga.estado = 'aceptado'
                    carga.revisado_por_id = revisado_por_pk
                    carga.fecha_revision = timezone.now()
                    carga.save()
        except Exception as e:
            # Si falló validando (dry_run), no hay nada útil que revisar
            # todavía: con_errores, hay que resubir. Si falló aplicando de
            # verdad (aceptar), el transaction.atomic() ya revirtió
            # cualquier cambio a servidores/plazas — regresa a
            # pendiente_revision para que puedan reintentar Aceptar.
            carga.estado = 'con_errores' if dry_run else 'pendiente_revision'
            carga.log_errores = f'Error inesperado durante el procesamiento en segundo plano:\n{e}'
            carga.save()
    finally:
        connection.close()


def _lanzar_procesamiento(carga_pk, dry_run, overrides=None, revisado_por_pk=None):
    hilo = threading.Thread(
        target=_procesar_carga_en_segundo_plano,
        args=(carga_pk, dry_run, overrides, revisado_por_pk),
        daemon=True,
    )
    hilo.start()

MESES_ES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
# Prioridad para cuando un día cae en la ventana de más de un período.
PRIORIDAD_ESTADO = {'verde': 0, 'dorado': 1, 'rojo': 2}


class CargaListView(LoginRequiredMixin, DependenciaScopedMixin, ListView):
    model = CargaLayout
    template_name = 'cargas/list.html'
    context_object_name = 'cargas'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Historial de Cargas'
        user = self.request.user
        ctx['puede_revisar_lista'] = user.es_administrador or user.rol == 'validador'
        return ctx


@login_required
def carga_layout(request):
    """La carga siempre es contra el período de carga activo (PeriodoCarga con
    activo=True); no se permite elegir otro desde este formulario. El TIPO de
    layout tampoco se elige aquí: llega fijo por querystring/POST desde los
    links del calendario (calendario_cargas) — Información Básica y Bajas
    están disponibles en cualquier quincena, Datos Personales solo en la
    segunda quincena de marzo (ver tipos_permitidos_periodo). Si no hay
    período activo, si hoy no cae dentro de la ventana de carga (ni de una
    excepción vigente para la dependencia del usuario), o si el tipo no es
    válido para el período activo, se avisa con un mensaje y se regresa al
    calendario en vez de mostrar el formulario."""
    periodo_activo = periodo_vigente_hoy()
    hoy = timezone.localdate()

    if not periodo_activo:
        messages.warning(request, 'No hay una fecha de carga disponible: no hay un período de carga activo. Solicite al administrador que configure uno.')
        return redirect('calendario_cargas')

    # Un usuario no-administrador tiene dependencia fija, así que su ventana
    # (ya sea la general del período o su excepción) se puede validar de una
    # vez, antes de mostrar el formulario. Un administrador puede elegir
    # cualquier dependencia en el formulario, así que esa validación se hace
    # hasta el POST, cuando ya se sabe cuál escogió.
    if not request.user.es_administrador:
        ini, fin = ventana_permitida(periodo_activo, request.user.dependencia)
        if not (ini <= hoy <= fin):
            messages.warning(
                request,
                f'No hay una fecha de carga disponible en este momento para {request.user.dependencia}: '
                f'la ventana de carga es del {ini} al {fin}. Si necesita cargar fuera de estas fechas, '
                f'solicite al administrador una excepción de acceso.'
            )
            return redirect('calendario_cargas')

    tipo = request.POST.get('tipo') if request.method == 'POST' else request.GET.get('tipo')
    tipos_ok = tipos_permitidos_periodo(periodo_activo)
    if tipo not in tipos_ok:
        messages.error(request, 'Elija el tipo de carga desde el calendario — no está disponible para el período activo.')
        return redirect('calendario_cargas')
    tipo_label = dict(CargaLayout.TIPO_CHOICES).get(tipo, tipo)

    if request.method == 'POST':
        form = CargaLayoutForm(request.POST, request.FILES)
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
        if form.is_valid():
            carga = form.save(commit=False)
            carga.tipo = tipo  # se fija con lo ya validado arriba, no con lo que traiga el POST
            carga.periodo = periodo_activo

            if not request.user.es_administrador and carga.dependencia_id != request.user.dependencia_id:
                messages.error(request, 'No tiene permiso para cargar información de otra dependencia.')
                return render(request, 'cargas/form.html', {
                    'form': form, 'titulo': f'Cargar {tipo_label}', 'periodo_activo': periodo_activo,
                    'tipo': tipo, 'tipo_label': tipo_label,
                })

            ini, fin = ventana_permitida(carga.periodo, carga.dependencia)
            if not (ini <= hoy <= fin):
                messages.warning(
                    request,
                    f'No hay una fecha de carga disponible para {carga.dependencia}: '
                    f'la ventana de carga es del {ini} al {fin}. Si necesita cargar fuera de estas fechas, '
                    f'solicite al administrador una excepción de acceso.'
                )
                return render(request, 'cargas/form.html', {
                    'form': form, 'titulo': f'Cargar {tipo_label}', 'periodo_activo': periodo_activo,
                    'tipo': tipo, 'tipo_label': tipo_label,
                })

            carga.usuario_carga = request.user
            carga.estado = 'procesando'
            carga.save()

            # ── Validar (vista previa) según tipo de layout ────────────────
            # Ojo: esto NO escribe en el padrón todavía; solo valida el
            # archivo. La aplicación real ocurre cuando el validador acepta
            # la carga (ver carga_aceptar). Corre en un hilo aparte (no en
            # este request) porque un archivo grande puede tardar más de lo
            # que nginx/gunicorn esperan una respuesta; la pantalla de
            # detalle se auto-refresca mientras estado == 'procesando'.
            _lanzar_procesamiento(carga.pk, dry_run=True)

            messages.info(
                request,
                'Archivo recibido, validándose en segundo plano — esta página se '
                'actualizará sola cuando termine.'
            )
            return redirect('carga_detalle', pk=carga.pk)
    else:
        form = CargaLayoutForm(initial={'tipo': tipo})
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
            form.fields['dependencia'].initial = request.user.dependencia_id
    return render(request, 'cargas/form.html', {
        'form': form, 'titulo': f'Cargar {tipo_label}', 'periodo_activo': periodo_activo,
        'tipo': tipo, 'tipo_label': tipo_label,
    })


@login_required
def carga_detalle(request, pk):
    qs = filtrar_por_dependencia(CargaLayout.objects.all(), request.user)
    carga = get_object_or_404(qs, pk=pk)
    # Parsear log en líneas para mostrar en tabla
    log_lines = []
    if carga.log_errores:
        for linea in carga.log_errores.split('\n'):
            linea = linea.strip()
            if not linea:
                continue
            if 'ERROR' in linea:
                tipo = 'error'
            elif 'OMITIDA' in linea:
                tipo = 'omitida'
            elif 'Aviso' in linea or 'Avisos' in linea:
                tipo = 'aviso'
            else:
                tipo = 'ok'
            log_lines.append({'texto': linea, 'tipo': tipo})

    # Cada fila con error/omitida se enriquece con su decisión de revisión
    # (si ya se tomó), para que la tabla y el gate de "Aceptar" no dependan
    # de hacer lookups de diccionario dentro del template.
    decisiones = carga.decisiones_filas or {}
    filas_vista = []
    pendientes = []
    for f in carga.detalle_filas:
        f2 = dict(f)
        if f.get('estado') in ('ERROR', 'OMITIDA'):
            d = decisiones.get(str(f.get('fila')))
            if d:
                f2['decision'] = d.get('decision')
                f2['decision_motivo'] = d.get('motivo')
                f2['decision_por'] = d.get('por')
            else:
                pendientes.append(f)
        filas_vista.append(f2)

    puede_aceptar = not pendientes and (
        carga.registros_ok > 0 or any(v.get('decision') == 'aceptada' for v in decisiones.values())
    )

    return render(request, 'cargas/detalle.html', {
        'carga': carga,
        'log_lines': log_lines,
        'titulo': 'Detalle de Carga',
        'puede_revisar': puede_revisar_carga(request.user, carga),
        'filas_vista': filas_vista,
        'pendientes_count': len(pendientes),
        'hay_no_forzables_pendientes': any(not f.get('forzable') for f in pendientes),
        'puede_aceptar': puede_aceptar,
    })


@login_required
def carga_revalidar(request, pk):
    """Vuelve a correr la validación (dry_run) sobre el mismo archivo ya
    subido, sin pedir que se resuba. Sirve para refrescar carga.detalle_filas
    en cargas que quedaron pendientes de revisión con una versión anterior
    del procesador — por ejemplo, antes de que existiera la marca 'forzable'
    por fila, esas cargas se quedaban sin poder mostrar el botón Aceptar en
    ningún error aunque fuera de los que sí se pueden forzar."""
    if request.method != 'POST':
        raise PermissionDenied
    carga = get_object_or_404(CargaLayout, pk=pk)
    if not puede_revisar_carga(request.user, carga):
        raise PermissionDenied
    if carga.estado != 'pendiente_revision':
        messages.error(request, 'Esta carga ya fue revisada o no está lista para revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    carga.estado = 'procesando'
    carga.save(update_fields=['estado'])
    _lanzar_procesamiento(carga.pk, dry_run=True)

    messages.info(
        request,
        'Re-validando en segundo plano — esta página se actualizará sola cuando termine.'
    )
    return redirect('carga_detalle', pk=carga.pk)


@login_required
def carga_comprobante(request, pk):
    """PDF de comprobante de la carga: resumen de período/dependencia,
    contadores de registros y, si los hay, el detalle de los que tuvieron
    error. Refleja el estado de la carga al momento de generarse."""
    qs = filtrar_por_dependencia(CargaLayout.objects.all(), request.user)
    carga = get_object_or_404(qs, pk=pk)
    pdf = generar_comprobante_pdf(carga)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="comprobante_carga_{carga.pk}.pdf"'
    return response


@login_required
def carga_decidir_fila(request, pk, fila):
    """El validador acepta o rechaza, fila por fila, un registro con error
    durante la revisión. 'Aceptar' solo es posible si el error es FORZABLE
    (RFC/CURP con formato inválido — hay un valor capturado) y exige motivo;
    el resto de los errores solo se pueden rechazar (quedan omitidos, como
    ya pasaba). La decisión queda guardada en carga.decisiones_filas."""
    if request.method != 'POST':
        raise PermissionDenied
    carga = get_object_or_404(CargaLayout, pk=pk)
    if not puede_revisar_carga(request.user, carga):
        raise PermissionDenied
    if carga.estado != 'pendiente_revision':
        messages.error(request, 'Esta carga ya fue revisada o no está lista para revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    fila_info = next((f for f in carga.detalle_filas if f.get('fila') == fila), None)
    if not fila_info or fila_info.get('estado') not in ('ERROR', 'OMITIDA'):
        messages.error(request, f'La fila {fila} no tiene un error pendiente de revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    decision = request.POST.get('decision')
    motivo = request.POST.get('motivo', '').strip()
    if decision not in ('aceptada', 'rechazada'):
        messages.error(request, 'Decisión inválida.')
        return redirect('carga_detalle', pk=carga.pk)
    if decision == 'aceptada':
        if not fila_info.get('forzable'):
            messages.error(request, f'La fila {fila} no se puede aceptar: el error no es de los que se pueden forzar.')
            return redirect('carga_detalle', pk=carga.pk)
        if not motivo:
            messages.error(request, 'Debe indicar un motivo para aceptar una fila con error.')
            return redirect('carga_detalle', pk=carga.pk)

    decisiones = dict(carga.decisiones_filas)
    decisiones[str(fila)] = {
        'decision': decision, 'motivo': motivo,
        'por': str(request.user), 'fecha': timezone.now().isoformat(),
    }
    carga.decisiones_filas = decisiones
    carga.save(update_fields=['decisiones_filas'])
    messages.success(request, f'Fila {fila}: decisión registrada ({decision}).')
    return redirect('carga_detalle', pk=carga.pk)


@login_required
def carga_rechazar_pendientes(request, pk):
    """Rechaza de un golpe todas las filas con error que NO se pueden forzar
    — no tiene caso pedir un clic por cada una si la única decisión posible
    ya es omitirlas; esto solo dispara ese mismo rechazo explícito en lote,
    sin tocar las filas forzables (esas sí requieren revisión individual)."""
    if request.method != 'POST':
        raise PermissionDenied
    carga = get_object_or_404(CargaLayout, pk=pk)
    if not puede_revisar_carga(request.user, carga):
        raise PermissionDenied
    if carga.estado != 'pendiente_revision':
        messages.error(request, 'Esta carga ya fue revisada o no está lista para revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    decisiones = dict(carga.decisiones_filas)
    marcadas = 0
    for f in carga.detalle_filas:
        if f.get('estado') in ('ERROR', 'OMITIDA') and not f.get('forzable'):
            clave = str(f['fila'])
            if clave not in decisiones:
                decisiones[clave] = {
                    'decision': 'rechazada', 'motivo': 'Rechazo en lote — error no forzable',
                    'por': str(request.user), 'fecha': timezone.now().isoformat(),
                }
                marcadas += 1
    carga.decisiones_filas = decisiones
    carga.save(update_fields=['decisiones_filas'])
    messages.success(request, f'{marcadas} fila(s) con error no forzable quedaron rechazadas.')
    return redirect('carga_detalle', pk=carga.pk)


@login_required
def carga_aceptar(request, pk):
    """El validador de la dependencia (o un administrador) acepta la carga:
    recién aquí se aplican de verdad los cambios al padrón."""
    if request.method != 'POST':
        raise PermissionDenied
    carga = get_object_or_404(CargaLayout, pk=pk)
    if not puede_revisar_carga(request.user, carga):
        raise PermissionDenied
    if carga.estado != 'pendiente_revision':
        messages.error(request, 'Esta carga ya fue revisada o no está lista para revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    # No se puede aceptar mientras queden filas con error sin revisar (cada
    # una necesita una decisión explícita: aceptada —solo si es forzable,
    # con motivo— o rechazada). Tampoco tiene sentido aceptar una carga que
    # no vaya a afectar ningún registro.
    filas_error = [f for f in carga.detalle_filas if f.get('estado') in ('ERROR', 'OMITIDA')]
    pendientes = [f for f in filas_error if str(f.get('fila')) not in carga.decisiones_filas]
    if pendientes:
        messages.error(
            request,
            f'No se puede aceptar: hay {len(pendientes)} registro(s) con error sin revisar. '
            f'Acepte o rechace cada uno abajo (o use "Rechazar pendientes no forzables").'
        )
        return redirect('carga_detalle', pk=carga.pk)

    hay_algo_que_aplicar = carga.registros_ok > 0 or any(
        v.get('decision') == 'aceptada' for v in carga.decisiones_filas.values()
    )
    if not hay_algo_que_aplicar:
        messages.error(request, 'No se puede aceptar: no hay ningún registro válido que aplicar al padrón.')
        return redirect('carga_detalle', pk=carga.pk)

    overrides = {int(k): v for k, v in carga.decisiones_filas.items()}

    # Aplicar de verdad al padrón corre en un hilo aparte, no en este
    # request (mismo motivo que al validar: un archivo grande puede tardar
    # más de lo que nginx/gunicorn esperan una respuesta). La pantalla de
    # detalle se auto-refresca mientras estado == 'procesando'.
    carga.estado = 'procesando'
    carga.save(update_fields=['estado'])
    _lanzar_procesamiento(carga.pk, dry_run=False, overrides=overrides, revisado_por_pk=request.user.pk)

    messages.info(
        request,
        'Aplicando los cambios al padrón en segundo plano — esta página se '
        'actualizará sola cuando termine.'
    )
    return redirect('carga_detalle', pk=carga.pk)


@login_required
def carga_rechazar(request, pk):
    """El validador de la dependencia (o un administrador) rechaza la carga:
    queda archivada con motivo y nunca toca el padrón."""
    if request.method != 'POST':
        raise PermissionDenied
    carga = get_object_or_404(CargaLayout, pk=pk)
    if not puede_revisar_carga(request.user, carga):
        raise PermissionDenied
    if carga.estado != 'pendiente_revision':
        messages.error(request, 'Esta carga ya fue revisada o no está lista para revisión.')
        return redirect('carga_detalle', pk=carga.pk)

    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, 'Debe indicar un motivo de rechazo.')
        return redirect('carga_detalle', pk=carga.pk)

    carga.estado = 'rechazado'
    carga.motivo_rechazo = motivo
    carga.revisado_por = request.user
    carga.fecha_revision = timezone.now()
    carga.save()

    messages.success(request, 'Carga rechazada. No se aplicó ningún cambio al padrón.')
    return redirect('carga_detalle', pk=carga.pk)


@login_required
def calendario_cargas(request):
    """Calendario de un solo mes (estilo Google Calendar): resalta los días
    en los que hay una ventana de carga abierta, próxima o cerrada para
    alguna quincena. Navega con ‹ › entre meses."""
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
        if not (1 <= mes <= 12):
            raise ValueError
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month

    primer_dia_mes = datetime.date(anio, mes, 1)
    ultimo_dia_mes = datetime.date(anio, mes, calendar.monthrange(anio, mes)[1])
    dia_anterior = primer_dia_mes - datetime.timedelta(days=1)
    dia_siguiente = ultimo_dia_mes + datetime.timedelta(days=1)

    # Trae también las quincenas del mes previo/siguiente: sus ventanas de
    # carga pueden caer sobre días que se muestran en esta cuadrícula.
    periodos = PeriodoCarga.objects.filter(
        fecha_inicio__year__in={anio, dia_anterior.year, dia_siguiente.year}
    )

    dias_ventana = {}
    for periodo in periodos:
        if periodo.fecha_fin <= hoy <= periodo.fecha_cierre:
            estado, color = 'Abierta ahora', 'verde'
        elif hoy < periodo.fecha_fin:
            estado, color = 'Próxima', 'dorado'
        else:
            estado, color = 'Cerrada', 'rojo'
        info = {
            'quincena': periodo.quincena,
            'ejercicio': periodo.ejercicio,
            'estado': estado, 'color': color,
        }
        dia = periodo.fecha_fin
        while dia <= periodo.fecha_cierre:
            actual = dias_ventana.get(dia)
            if actual is None or PRIORIDAD_ESTADO[color] < PRIORIDAD_ESTADO[actual['color']]:
                dias_ventana[dia] = info
            dia += datetime.timedelta(days=1)

    cal = calendar.Calendar(firstweekday=0)
    semanas = []
    semana_actual = []
    for fecha in cal.itermonthdates(anio, mes):
        semana_actual.append({
            'fecha': fecha,
            'numero': fecha.day,
            'es_mes_actual': fecha.month == mes,
            'es_hoy': fecha == hoy,
            'es_finde': fecha.weekday() >= 5,
            'ventana': dias_ventana.get(fecha),
        })
        if len(semana_actual) == 7:
            semanas.append(semana_actual)
            semana_actual = []

    # ── Panel "Acciones de hoy": único punto de entrada para cargar layouts,
    # reemplaza el link genérico "Cargar Layout" (ya no se elige el tipo en
    # un formulario, se elige aquí según lo que esté permitido ahora mismo).
    periodo_activo = periodo_vigente_hoy()
    ventana_ini = ventana_fin = None
    ventana_abierta = False
    tipos_disponibles = []
    if periodo_activo:
        if request.user.es_administrador:
            # El admin no tiene dependencia fija: la ventana real se valida
            # por dependencia hasta que la elija en el formulario, así que
            # aquí los links quedan siempre habilitados.
            ventana_ini, ventana_fin = periodo_activo.fecha_fin, periodo_activo.fecha_cierre
            ventana_abierta = True
        else:
            ventana_ini, ventana_fin = ventana_permitida(periodo_activo, request.user.dependencia)
            ventana_abierta = ventana_ini <= hoy <= ventana_fin
        if ventana_abierta:
            etiquetas_tipo = dict(CargaLayout.TIPO_CHOICES)
            tipos_disponibles = [
                {'tipo': t, 'label': etiquetas_tipo.get(t, t)}
                for t in tipos_permitidos_periodo(periodo_activo)
            ]

    return render(request, 'cargas/calendario.html', {
        'semanas': semanas,
        'dias_semana': DIAS_SEMANA,
        'nombre_mes': MESES_ES[mes],
        'anio': anio,
        'mes': mes,
        'anio_anterior': dia_anterior.year, 'mes_anterior': dia_anterior.month,
        'anio_siguiente': dia_siguiente.year, 'mes_siguiente': dia_siguiente.month,
        'es_mes_actual': (anio == hoy.year and mes == hoy.month),
        'titulo': 'Calendario de Cargas',
        'periodo_activo': periodo_activo,
        'ventana_ini': ventana_ini,
        'ventana_fin': ventana_fin,
        'ventana_abierta': ventana_abierta,
        'tipos_disponibles': tipos_disponibles,
    })


class PeriodoCargaListView(LoginRequiredMixin, ListView):
    model = PeriodoCarga
    template_name = 'cargas/periodo_list.html'
    context_object_name = 'periodos'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Períodos de Carga'
        ctx['ejercicio_sugerido'] = timezone.localdate().year
        return ctx


class PeriodoCargaCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoCarga
    form_class = PeriodoCargaForm
    template_name = 'cargas/periodo_form.html'
    success_url = reverse_lazy('periodo_list')


@login_required
@admin_requerido
def generar_periodos(request):
    """Crea de un golpe los 24 períodos quincenales de un ejercicio."""
    if request.method == 'POST':
        form = GenerarPeriodosForm(request.POST)
        if form.is_valid():
            ejercicio = form.cleaned_data['ejercicio']
            creados, existentes = generar_periodos_ejercicio(ejercicio)
            if creados:
                messages.success(request, f'Se crearon {creados} períodos quincenales del ejercicio {ejercicio}.')
            if existentes:
                messages.info(request, f'{existentes} períodos de {ejercicio} ya existían y no se modificaron.')
        else:
            messages.error(request, 'Indique un ejercicio válido.')
    return redirect('periodo_list')


@login_required
@admin_requerido
def activar_periodo(request, pk):
    """Marca 'pk' como el período de carga activo. PeriodoCarga.save() ya
    garantiza que solo puede haber uno activo a la vez (desactiva el resto),
    así que aquí basta con guardar este con activo=True."""
    if request.method != 'POST':
        raise PermissionDenied
    periodo = get_object_or_404(PeriodoCarga, pk=pk)
    periodo.activo = True
    periodo.save()
    messages.success(
        request,
        f'Quincena {periodo.quincena}/{periodo.ejercicio} marcada como el período de carga activo.'
    )
    return redirect('periodo_list')


class AccesoExcepcionListView(AdministradorRequiredMixin, ListView):
    model = AccesoExcepcionCarga
    template_name = 'cargas/excepcion_list.html'
    context_object_name = 'excepciones'

    def get_queryset(self):
        return AccesoExcepcionCarga.objects.select_related('periodo', 'dependencia', 'autorizado_por')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excepciones de Acceso'
        return ctx


class AccesoExcepcionCreateView(AdministradorRequiredMixin, CreateView):
    model = AccesoExcepcionCarga
    form_class = AccesoExcepcionCargaForm
    template_name = 'cargas/excepcion_form.html'
    success_url = reverse_lazy('excepcion_list')

    def form_valid(self, form):
        form.instance.autorizado_por = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Excepción de Acceso'
        return ctx


class AccesoExcepcionDeleteView(AdministradorRequiredMixin, DeleteView):
    model = AccesoExcepcionCarga
    template_name = 'cargas/excepcion_confirm_delete.html'
    success_url = reverse_lazy('excepcion_list')


@login_required
def descargar_plantilla(request, tipo):
    """Sirve el archivo de plantilla Excel para el tipo de layout solicitado."""
    import os
    from django.http import FileResponse, Http404

    nombres = {
        'basica':      'Layout_Informacion_Basica.xlsx',
        'personales':  'Layout_Datos_Personales.xlsx',
        'bajas':       'Layout_Bajas.xlsx',
    }
    if tipo not in nombres:
        raise Http404("Plantilla no encontrada.")

    nombre_archivo = nombres[tipo]
    # Buscar el archivo en la raíz del proyecto
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base, nombre_archivo)

    if not os.path.exists(ruta):
        raise Http404(f"El archivo {nombre_archivo} no está disponible en el servidor.")

    response = FileResponse(
        open(ruta, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response
