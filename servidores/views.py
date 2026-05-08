# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from .models import ServidorPublico, InformacionBasica, BajaServidorPublico
from .forms import ServidorPublicoForm, InformacionBasicaForm, BajaForm
from catalogos.models import Dependencia
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
    model = ServidorPublico
    form_class = ServidorPublicoForm
    template_name = 'servidores/form.html'

    def get_success_url(self):
        return reverse_lazy('servidor_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Modificar: {self.object.nombre_completo}'
        ctx['accion'] = 'Guardar cambios'
        return ctx


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


class InformacionBasicaCreateView(LoginRequiredMixin, CreateView):
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Información Básica'
        return ctx


class InformacionBasicaUpdateView(LoginRequiredMixin, UpdateView):
    model = InformacionBasica
    form_class = InformacionBasicaForm
    template_name = 'servidores/info_basica_form.html'
    success_url = reverse_lazy('info_basica_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Modificar Información Básica'
        return ctx
