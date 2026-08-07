# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
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
from cargas.models import PeriodoCarga


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
    }
    return render(request, 'dashboard.html', context)


class ServidorListView(LoginRequiredMixin, ListView):
    model = ServidorPublico
    template_name = 'servidores/list.html'
    context_object_name = 'servidores'
    paginate_by = 20

    def get_queryset(self):
        qs = ServidorPublico.objects.filter(activo=True)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(primer_apellido__icontains=q) |
                Q(rfc__icontains=q) | Q(curp__icontains=q) | Q(expediente__icontains=q)
            )
        dep = self.request.GET.get('dependencia', '')
        if dep:
            qs = qs.filter(informacion_basica__dependencia_id=dep, informacion_basica__activo=True)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['dependencias'] = Dependencia.objects.all()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['titulo'] = 'Padrón de Servidores Públicos'
        return ctx


class ServidorDetailView(LoginRequiredMixin, DetailView):
    model = ServidorPublico
    template_name = 'servidores/detail.html'
    context_object_name = 'servidor'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['info_basica'] = InformacionBasica.objects.filter(
            servidor=self.object, activo=True
        ).order_by('-quincena').first()
        ctx['historial'] = InformacionBasica.objects.filter(
            servidor=self.object
        ).order_by('-quincena')[:10]
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


class ServidorUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de un Servidor Público, incluyendo los datos de la sección
    'Datos del Servidor Público' (domicilio, escolaridad, discapacidades,
    pueblo indígena, enfermedades crónicas e idiomas), que solo tiene sentido
    capturar sobre un servidor ya existente."""
    model = ServidorPublico
    form_class = ServidorPublicoForm
    template_name = 'servidores/form.html'

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
    servidor = get_object_or_404(ServidorPublico, pk=pk)
    if request.method == 'POST':
        form = BajaForm(request.POST)
        if form.is_valid():
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
    return render(request, 'servidores/baja_form.html', {
        'form': form, 'servidor': servidor, 'titulo': f'Registrar Baja: {servidor.nombre_completo}'
    })


@login_required
def hoja_resp(request, pk):
    servidor = get_object_or_404(ServidorPublico, pk=pk)
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
        qs = InformacionBasica.objects.filter(activo=True).select_related(
            'servidor', 'dependencia', 'estatus_plaza'
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
        qs = Puesto.objects.select_related(
            'proyecto', 'proyecto__dependencia', 'programa', 'programa__unidad',
            'unidad', 'categoria', 'servidor_actual', 'estatus_plaza'
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

        resumen = list(
            Puesto.objects.values('estatus_plaza__descripcion').annotate(total=Count('id')).order_by('-total')
        )
        for item in resumen:
            item['descripcion'] = item['estatus_plaza__descripcion'] or 'Sin estatus'
            item['icono'], item['color'] = ICONOS_ESTATUS_PLAZA.get(item['descripcion'].strip().lower(), ('📌', 'azul'))
        ctx['resumen_estatus'] = resumen
        ctx['total_plazas'] = Puesto.objects.count()
        return ctx


class PuestoUpdateView(LoginRequiredMixin, UpdateView):
    model = Puesto
    form_class = PuestoForm
    template_name = 'servidores/puesto_form.html'
    success_url = reverse_lazy('puesto_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Modificar Plaza: {self.object.id_plaza}'
        return ctx


class InformacionBasicaCreateView(LoginRequiredMixin, CreateView):
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Información Básica'
        return ctx

    def form_valid(self, form):
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


class InformacionBasicaUpdateView(LoginRequiredMixin, UpdateView):
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Modificar Información Básica'
        return ctx

    def form_valid(self, form):
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
