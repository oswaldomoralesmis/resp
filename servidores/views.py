# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q, Count
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from .models import (
    ServidorPublico, InformacionBasica, BajaServidorPublico, Puesto,
    DatosPersonales, DatosComplementarios, DiscapacidadServidor,
    EnfermedadCronicaServidor, IdiomaServidor,
    sincronizar_puesto, liberar_puestos_de,
)
from .forms import (
    ServidorPublicoForm, DatosPersonalesForm, DatosComplementariosForm,
    InformacionBasicaForm, BajaForm, PuestoForm,
)
from catalogos.models import Dependencia, EstatusPlaza, Discapacidad, EnfermedadCronica, Idioma
from cargas.models import PeriodoCarga, CargaLayout
from usuarios.mixins import DependenciaScopedMixin, filtrar_por_dependencia, admin_requerido


@login_required
def redirect_to_dashboard(request):
    return redirect('dashboard')

@login_required
def dashboard(request):
    total_servidores = ServidorPublico.objects.filter(activo=True).count()
    total_dependencias = Dependencia.objects.count()
    # últimas cargas
    periodo_actual = PeriodoCarga.objects.filter(activo=True).first()
    # estadísticas por estatus
    stats_estatus = InformacionBasica.objects.filter(
        activo=True
    ).values('estatus_plaza__descripcion').annotate(total=Count('id')).order_by('-total')[:5]

    context = {
        'total_servidores': total_servidores,
        'total_dependencias': total_dependencias,
        'periodo_actual': periodo_actual,
        'stats_estatus': stats_estatus,
        'titulo': 'Dashboard',
        'debug_mode': settings.DEBUG,
    }
    return render(request, 'dashboard.html', context)


@login_required
@admin_requerido
def reset_datos_prueba(request):
    """Borra todos los datos transaccionales (información básica, bajas,
    plazas, servidores, cargas y períodos) para dejar el ambiente listo para
    volver a probar desde cero. NO toca catálogos ni usuarios. Solo disponible
    con DEBUG=True (ambiente de desarrollo/pruebas), nunca en producción."""
    if not settings.DEBUG:
        raise Http404()

    conteos = {
        'Información Básica (historial quincenal)': InformacionBasica.objects.count(),
        'Bajas de Servidores': BajaServidorPublico.objects.count(),
        'Plazas': Puesto.objects.count(),
        'Servidores Públicos': ServidorPublico.objects.count(),
        'Cargas de Layouts': CargaLayout.objects.count(),
        'Períodos de Carga': PeriodoCarga.objects.count(),
    }

    if request.method == 'POST':
        with transaction.atomic():
            InformacionBasica.objects.all().delete()
            BajaServidorPublico.objects.all().delete()
            Puesto.objects.all().delete()
            ServidorPublico.objects.all().delete()
            CargaLayout.objects.all().delete()
            PeriodoCarga.objects.all().delete()
        messages.success(
            request,
            'Se eliminaron todos los servidores, plazas, información básica, bajas, cargas y '
            'períodos. Los catálogos y los usuarios del sistema no se modificaron.'
        )
        return redirect('dashboard')

    return render(request, 'servidores/reset_confirm.html', {
        'titulo': 'Reiniciar Datos de Prueba',
        'conteos': conteos,
        'total': sum(conteos.values()),
    })


class ServidorListView(LoginRequiredMixin, ListView):
    model = ServidorPublico
    template_name = 'servidores/list.html'
    context_object_name = 'servidores'
    paginate_by = 20

    def get_queryset(self):
        qs = ServidorPublico.objects.all()
        estatus = self.request.GET.get('estatus', 'activos')
        if estatus == 'activos':
            qs = qs.filter(activo=True)
        elif estatus == 'inactivos':
            qs = qs.filter(activo=False)
        # 'todos': sin filtro de activo.

        # Ojo: el filtro de dependencia NO exige informacion_basica__activo=True
        # — un servidor dado de baja tiene su Información Básica desactivada,
        # pero sigue perteneciendo históricamente a esa dependencia. Exigir
        # activo=True aquí lo dejaría invisible incluso para su propia
        # dependencia al buscarlo como inactivo/baja.
        user = self.request.user
        if not user.es_administrador:
            qs = qs.filter(informacion_basica__dependencia_id=user.dependencia_id)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(primer_apellido__icontains=q) |
                Q(rfc__icontains=q) | Q(curp__icontains=q) | Q(expediente__icontains=q)
            )
        dep = self.request.GET.get('dependencia', '')
        if dep:
            qs = qs.filter(informacion_basica__dependencia_id=dep)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['dependencias'] = filtrar_por_dependencia(Dependencia.objects.all(), self.request.user, 'pk')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['estatus'] = self.request.GET.get('estatus', 'activos')
        ctx['titulo'] = 'Padrón de Servidores Públicos'
        return ctx


class ServidorDetailView(LoginRequiredMixin, DependenciaScopedMixin, DetailView):
    model = ServidorPublico
    template_name = 'servidores/detail.html'
    context_object_name = 'servidor'
    dependencia_lookup = 'informacion_basica__dependencia_id'

    def get_queryset(self):
        return super().get_queryset().distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['info_basica'] = InformacionBasica.objects.filter(
            servidor=self.object, activo=True
        ).order_by('-quincena').first()
        ctx['historial'] = InformacionBasica.objects.filter(
            servidor=self.object
        ).order_by('-quincena')[:10]
        ctx['bajas'] = self.object.bajas.select_related('motivo_baja', 'dependencia').order_by('-fecha_baja')
        ctx['titulo'] = f'Servidor: {self.object.nombre_completo}'
        return ctx


class ServidorCreateView(LoginRequiredMixin, CreateView):
    model = ServidorPublico
    form_class = ServidorPublicoForm
    template_name = 'servidores/form.html'
    success_url = reverse_lazy('servidor_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Alta de Servidor Público'
        ctx['accion'] = 'Registrar'
        return ctx


class ServidorUpdateView(LoginRequiredMixin, DependenciaScopedMixin, UpdateView):
    """Edición de un Servidor Público, incluyendo los datos de la sección
    'Datos del Servidor Público' (domicilio, escolaridad, discapacidades,
    pueblo indígena, enfermedades crónicas e idiomas), que solo tiene sentido
    capturar sobre un servidor ya existente."""
    model = ServidorPublico
    form_class = ServidorPublicoForm
    template_name = 'servidores/form.html'
    dependencia_lookup = 'informacion_basica__dependencia_id'

    def get_queryset(self):
        return super().get_queryset().distinct()

    def get_success_url(self):
        return reverse_lazy('servidor_detail', kwargs={'pk': self.object.pk})

    @staticmethod
    def _checkboxes(catalogo_qs, seleccionados, niveles=None):
        """Lista de {pk, texto, checked, nivel} para renderizar un checklist.
        Normaliza a texto porque 'seleccionados'/'niveles' vienen a veces de
        POST (strings) y a veces de la BD (ids)."""
        seleccionados = {str(s) for s in seleccionados}
        niveles = {str(k): v for k, v in (niveles or {}).items()}
        return [
            {
                'pk': item.pk,
                'texto': str(item),
                'checked': str(item.pk) in seleccionados,
                'nivel': niveles.get(str(item.pk), ''),
            }
            for item in catalogo_qs
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Modificar: {self.object.nombre_completo}'
        ctx['accion'] = 'Guardar cambios'
        ctx.setdefault('form_personales', DatosPersonalesForm(instance=getattr(self.object, 'datos_personales', None)))
        ctx.setdefault('form_complementarios', DatosComplementariosForm(instance=getattr(self.object, 'datos_complementarios', None)))
        ctx.setdefault('discapacidades', self._checkboxes(
            Discapacidad.objects.all(), set(self.object.discapacidades.values_list('discapacidad_id', flat=True))
        ))
        ctx.setdefault('enfermedades', self._checkboxes(
            EnfermedadCronica.objects.all(), set(self.object.enfermedades.values_list('enfermedad_id', flat=True))
        ))
        ctx.setdefault('idiomas', self._checkboxes(
            Idioma.objects.all(), set(self.object.idiomas.values_list('idioma_id', flat=True)),
            niveles={r.idioma_id: r.nivel for r in self.object.idiomas.all()}
        ))
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        form_personales = DatosPersonalesForm(request.POST, instance=getattr(self.object, 'datos_personales', None))
        form_complementarios = DatosComplementariosForm(request.POST, instance=getattr(self.object, 'datos_complementarios', None))

        if form.is_valid() and form_personales.is_valid() and form_complementarios.is_valid():
            self.object = form.save()

            datos_personales = form_personales.save(commit=False)
            datos_personales.servidor = self.object
            datos_personales.save()

            datos_complementarios = form_complementarios.save(commit=False)
            datos_complementarios.servidor = self.object
            datos_complementarios.save()

            disc_ids = request.POST.getlist('discapacidades')
            self.object.discapacidades.all().delete()
            DiscapacidadServidor.objects.bulk_create([
                DiscapacidadServidor(servidor=self.object, discapacidad_id=pk) for pk in disc_ids
            ])

            enf_ids = request.POST.getlist('enfermedades')
            self.object.enfermedades.all().delete()
            EnfermedadCronicaServidor.objects.bulk_create([
                EnfermedadCronicaServidor(servidor=self.object, enfermedad_id=pk) for pk in enf_ids
            ])

            idioma_ids = request.POST.getlist('idiomas')
            self.object.idiomas.all().delete()
            IdiomaServidor.objects.bulk_create([
                IdiomaServidor(servidor=self.object, idioma_id=pk, nivel=request.POST.get(f'nivel_idioma_{pk}', '').strip())
                for pk in idioma_ids
            ])

            return redirect(self.get_success_url())

        niveles_post = {
            pk: request.POST.get(f'nivel_idioma_{pk}', '').strip() for pk in request.POST.getlist('idiomas')
        }
        return self.render_to_response(self.get_context_data(
            form=form, form_personales=form_personales, form_complementarios=form_complementarios,
            discapacidades=self._checkboxes(Discapacidad.objects.all(), set(request.POST.getlist('discapacidades'))),
            enfermedades=self._checkboxes(EnfermedadCronica.objects.all(), set(request.POST.getlist('enfermedades'))),
            idiomas=self._checkboxes(Idioma.objects.all(), set(request.POST.getlist('idiomas')), niveles=niveles_post),
        ))


@login_required
def servidor_baja(request, pk):
    qs = filtrar_por_dependencia(
        ServidorPublico.objects.all(), request.user, 'informacion_basica__dependencia_id'
    ).distinct()
    servidor = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        form = BajaForm(request.POST)
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
        if form.is_valid():
            if not request.user.es_administrador and form.cleaned_data['dependencia'].pk != request.user.dependencia_id:
                form.add_error('dependencia', 'No tiene permiso para asignar esta dependencia.')
            else:
                baja = form.save(commit=False)
                baja.servidor = servidor
                baja.registrado_por = request.user
                baja.save()
                servidor.activo = False
                servidor.save()
                InformacionBasica.objects.filter(servidor=servidor, activo=True).update(activo=False)
                liberar_puestos_de(servidor)
                return redirect('servidor_list')
    else:
        form = BajaForm()
        if not request.user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(
                pk=request.user.dependencia_id
            )
            form.fields['dependencia'].initial = request.user.dependencia_id
    return render(request, 'servidores/baja_form.html', {
        'form': form, 'servidor': servidor, 'titulo': f'Registrar Baja: {servidor.nombre_completo}'
    })


@login_required
def hoja_resp(request, pk):
    qs = filtrar_por_dependencia(
        ServidorPublico.objects.all(), request.user, 'informacion_basica__dependencia_id'
    ).distinct()
    servidor = get_object_or_404(qs, pk=pk)
    info = InformacionBasica.objects.filter(servidor=servidor, activo=True).order_by('-quincena').first()
    return render(request, 'servidores/hoja_resp.html', {
        'servidor': servidor, 'info': info, 'titulo': 'Hoja RESP'
    })


class InformacionBasicaListView(LoginRequiredMixin, ListView):
    model = InformacionBasica
    template_name = 'servidores/info_basica_list.html'
    context_object_name = 'registros'
    paginate_by = 25

    def get_queryset(self):
        qs = filtrar_por_dependencia(
            InformacionBasica.objects.filter(activo=True).select_related('servidor', 'dependencia', 'estatus_plaza'),
            self.request.user,
        )
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(servidor__nombre__icontains=q) | Q(servidor__rfc__icontains=q) |
                Q(id_plaza__icontains=q)
            )
        return qs.order_by('-quincena')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Información Básica'
        return ctx


ICONOS_ESTATUS_PLAZA = {
    'ocupada':     ('👤', 'verde'),
    'vacante':     ('🪑', 'rojo'),
    'licencia':    ('🌴', 'dorado'),
    'comisionado': ('🔄', 'azul'),
    'reservada':   ('🔒', 'azul'),
    'suspendido':  ('⛔', 'rojo'),
}


class PuestoListView(LoginRequiredMixin, ListView):
    model = Puesto
    template_name = 'servidores/puesto_list.html'
    context_object_name = 'puestos'
    paginate_by = 25

    def get_queryset(self):
        qs = filtrar_por_dependencia(
            Puesto.objects.select_related(
                'proyecto', 'proyecto__dependencia', 'programa', 'programa__unidad',
                'unidad', 'categoria', 'servidor_actual', 'estatus_plaza'
            ),
            self.request.user, 'proyecto__dependencia',
        )
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(id_plaza__icontains=q) | Q(proyecto__clave__icontains=q) |
                Q(proyecto__dependencia__clave__icontains=q) |
                Q(servidor_actual__rfc__icontains=q)
            )
        estatus = self.request.GET.get('estatus', '')
        if estatus:
            qs = qs.filter(estatus_plaza_id=estatus)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Plazas'
        ctx['q'] = self.request.GET.get('q', '')
        ctx['estatus'] = self.request.GET.get('estatus', '')
        ctx['estatus_choices'] = EstatusPlaza.objects.all()

        puestos_visibles = filtrar_por_dependencia(Puesto.objects.all(), self.request.user, 'proyecto__dependencia')
        resumen = list(
            puestos_visibles.values('estatus_plaza__descripcion').annotate(total=Count('id')).order_by('-total')
        )
        for item in resumen:
            item['descripcion'] = item['estatus_plaza__descripcion'] or 'Sin estatus'
            item['icono'], item['color'] = ICONOS_ESTATUS_PLAZA.get(item['descripcion'].strip().lower(), ('📌', 'azul'))
        ctx['resumen_estatus'] = resumen
        ctx['total_plazas'] = puestos_visibles.count()
        return ctx


class PuestoUpdateView(LoginRequiredMixin, DependenciaScopedMixin, UpdateView):
    model = Puesto
    form_class = PuestoForm
    template_name = 'servidores/puesto_form.html'
    success_url = reverse_lazy('puesto_list')
    dependencia_lookup = 'proyecto__dependencia'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Modificar Plaza: {self.object.id_plaza}'
        return ctx

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(pk=user.dependencia_id)
            form.fields['dependencia'].initial = user.dependencia_id
            for campo in ('proyecto', 'programa', 'unidad'):
                form.fields[campo].queryset = form.fields[campo].queryset.filter(dependencia_id=user.dependencia_id)
        return form

    def form_valid(self, form):
        user = self.request.user
        if not user.es_administrador:
            proyecto = form.cleaned_data.get('proyecto')
            if proyecto and proyecto.dependencia_id != user.dependencia_id:
                form.add_error('proyecto', 'No tiene permiso para asignar un proyecto de otra dependencia.')
                return self.form_invalid(form)
        return super().form_valid(form)


class InformacionBasicaCreateView(LoginRequiredMixin, CreateView):
    """No usa DependenciaFormRestrictMixin: su form_valid() ya está sobrescrito
    para sincronizar la Plaza tras guardar, y esa sincronización no debe
    ejecutarse si la validación de dependencia rechaza el POST. Se valida
    explícito al inicio de este mismo form_valid en su lugar."""
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if 'dependencia' in form.fields and not user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(pk=user.dependencia_id)
            form.fields['dependencia'].initial = user.dependencia_id
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Información Básica'
        return ctx

    def form_valid(self, form):
        user = self.request.user
        if not user.es_administrador:
            dep = form.cleaned_data.get('dependencia')
            if dep and dep.pk != user.dependencia_id:
                form.add_error('dependencia', 'No tiene permiso para asignar esta dependencia.')
                return self.form_invalid(form)
        response = super().form_valid(form)
        info = self.object
        sincronizar_puesto(
            info.proyecto, info.programa, info.id_plaza, info.categoria, info.servidor,
            unidad=info.unidad,
            nombramiento=info.nombramiento,
            nivel_estructura=info.nivel_estructura,
            estatus_plaza=info.estatus_plaza,
            cct=info.cct,
            hsm=info.hsm,
            total_percepciones=info.total_percepciones,
            total_bonos=info.total_bonos,
            total_neto=info.total_neto,
            dias_pagados=info.dias_pagados,
            id_plaza_jefe=info.id_plaza_jefe,
        )
        return response


class InformacionBasicaUpdateView(LoginRequiredMixin, DependenciaScopedMixin, UpdateView):
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if 'dependencia' in form.fields and not user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(pk=user.dependencia_id)
            form.fields['dependencia'].initial = user.dependencia_id
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Modificar Información Básica'
        return ctx

    def form_valid(self, form):
        user = self.request.user
        if not user.es_administrador:
            dep = form.cleaned_data.get('dependencia')
            if dep and dep.pk != user.dependencia_id:
                form.add_error('dependencia', 'No tiene permiso para asignar esta dependencia.')
                return self.form_invalid(form)
        response = super().form_valid(form)
        info = self.object
        sincronizar_puesto(
            info.proyecto, info.programa, info.id_plaza, info.categoria, info.servidor,
            unidad=info.unidad,
            nombramiento=info.nombramiento,
            nivel_estructura=info.nivel_estructura,
            estatus_plaza=info.estatus_plaza,
            cct=info.cct,
            hsm=info.hsm,
            total_percepciones=info.total_percepciones,
            total_bonos=info.total_bonos,
            total_neto=info.total_neto,
            dias_pagados=info.dias_pagados,
            id_plaza_jefe=info.id_plaza_jefe,
        )
        return response
