# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import CargaLayout, PeriodoCarga
from .forms import CargaLayoutForm, PeriodoCargaForm
from .procesador import procesar_layout_basica


class CargaListView(LoginRequiredMixin, ListView):
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
    if request.method == 'POST':
        form = CargaLayoutForm(request.POST, request.FILES)
        if form.is_valid():
            carga = form.save(commit=False)
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
    return render(request, 'cargas/form.html', {'form': form, 'titulo': 'Cargar Layout'})


@login_required
def carga_detalle(request, pk):
    carga = get_object_or_404(CargaLayout, pk=pk)
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
    periodos = PeriodoCarga.objects.all().order_by('-quincena')[:24]
    return render(request, 'cargas/calendario.html', {
        'periodos': periodos,
        'titulo': 'Calendario de Cargas',
    })


class PeriodoCargaListView(LoginRequiredMixin, ListView):
    model = PeriodoCarga
    template_name = 'cargas/periodo_list.html'
    context_object_name = 'periodos'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Períodos de Carga'
        return ctx


class PeriodoCargaCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoCarga
    form_class = PeriodoCargaForm
    template_name = 'cargas/periodo_form.html'
    success_url = reverse_lazy('periodo_list')


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
