# -*- coding: utf-8 -*-
import calendar
import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone

from .models import CargaLayout, PeriodoCarga, AccesoExcepcionCarga, ventana_permitida, generar_periodos_ejercicio
from .forms import CargaLayoutForm, PeriodoCargaForm, AccesoExcepcionCargaForm, GenerarPeriodosForm
from .procesador import procesar_layout_basica
from usuarios.mixins import AdministradorRequiredMixin, DependenciaScopedMixin, filtrar_por_dependencia, admin_requerido

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
        return ctx


@login_required
def carga_layout(request):
    """La carga siempre es contra el período de carga activo (PeriodoCarga con
    activo=True); no se permite elegir otro desde este formulario. Si no hay
    período activo, o si hoy no cae dentro de su ventana de carga (ni de una
    excepción vigente para la dependencia del usuario), se avisa con un
    warning y no se deja pasar al formulario de carga."""
    periodo_activo = PeriodoCarga.objects.filter(activo=True).first()
    hoy = timezone.localdate()

    if not periodo_activo:
        messages.warning(request, 'No hay una fecha de carga disponible: no hay un período de carga activo. Solicite al administrador que configure uno.')
        return redirect('carga_list')

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
            return redirect('carga_list')

    if request.method == 'POST':
        form = CargaLayoutForm(request.POST, request.FILES)
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
        if form.is_valid():
            carga = form.save(commit=False)
            carga.periodo = periodo_activo

            if not request.user.es_administrador and carga.dependencia_id != request.user.dependencia_id:
                messages.error(request, 'No tiene permiso para cargar información de otra dependencia.')
                return render(request, 'cargas/form.html', {
                    'form': form, 'titulo': 'Cargar Layout', 'periodo_activo': periodo_activo,
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
                    'form': form, 'titulo': 'Cargar Layout', 'periodo_activo': periodo_activo,
                })

            carga.usuario_carga = request.user
            carga.estado = 'procesando'
            carga.save()

            # ── Procesar según tipo de layout ─────────────────────────────
            try:
                if carga.tipo == 'basica':
                    resultado = procesar_layout_basica(carga)
                else:
                    # Tipos futuros: personales, bajas
                    resultado = {'ok': 0, 'errores': 0, 'total': 0,
                                 'log': f'Tipo "{carga.tipo}" aún no implementado.'}

                carga.registros_totales = resultado['total']
                carga.registros_ok      = resultado['ok']
                carga.registros_error   = resultado['errores']
                carga.log_errores       = resultado['log']
                carga.estado = 'completado' if resultado['errores'] == 0 else 'con_errores'
                carga.save()

                if resultado['errores'] == 0:
                    messages.success(
                        request,
                        f'Layout procesado correctamente. '
                        f'{resultado["ok"]} registros cargados al padrón.'
                    )
                else:
                    messages.warning(
                        request,
                        f'Layout procesado con observaciones. '
                        f'{resultado["ok"]} correctos, '
                        f'{resultado["errores"]} con error de {resultado["total"]} totales.'
                    )

            except Exception as e:
                carga.estado = 'con_errores'
                carga.log_errores = f'Error inesperado durante el procesamiento:\n{e}'
                carga.save()
                messages.error(request, f'Error al procesar el archivo: {e}')

            return redirect('carga_detalle', pk=carga.pk)
    else:
        form = CargaLayoutForm()
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
            form.fields['dependencia'].initial = request.user.dependencia_id
    return render(request, 'cargas/form.html', {
        'form': form, 'titulo': 'Cargar Layout', 'periodo_activo': periodo_activo,
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

    return render(request, 'cargas/detalle.html', {
        'carga': carga,
        'log_lines': log_lines,
        'titulo': 'Detalle de Carga',
    })


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
