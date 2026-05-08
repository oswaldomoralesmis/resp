# -*- coding: utf-8 -*-
import os
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from django.db.models import Q

from catalogos.models import (
    Dependencia, Categoria, UnidadAdministrativa,
    Programa, Proyecto,
)


def catalogo_index(request):
    catalogos = [
        {'nombre': 'Categorías',              'url': 'categoria_list',   'icono': '🏷️',  'desc': 'Claves y descripciones de categorías de puestos',    'descarga': 'categoria'},
        {'nombre': 'Unidades Administrativas','url': 'unidad_list',      'icono': '🏢',  'desc': 'Unidades por dependencia con clave de 8 dígitos',     'descarga': 'unidades'},
        {'nombre': 'Programas',               'url': 'programa_list',    'icono': '📋',  'desc': 'Programas presupuestales por dependencia y unidad',   'descarga': 'programas'},
        {'nombre': 'Proyectos',               'url': 'proyecto_list',    'icono': '📁',  'desc': 'Proyectos ligados a programa, unidad y dependencia',  'descarga': 'proyectos'},
        {'nombre': 'Dependencias',            'url': 'dependencia_list', 'icono': '🏛️',  'desc': 'Dependencias del Gobierno del Estado de Tabasco',    'descarga': None},
    ]
    return render(request, 'catalogos/index.html', {
        'titulo': 'Catálogos del Sistema',
        'catalogos': catalogos,
    })


# ── Dependencias ──────────────────────────────────────────────────────────────
class DependenciaListView(LoginRequiredMixin, ListView):
    model = Dependencia
    template_name = 'catalogos/list_generica.html'
    context_object_name = 'registros'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Dependencias', 'columnas': ['Ejercicio', 'Clave', 'Descripción'],
                    'create_url': 'dependencia_create', 'update_url': 'dependencia_update',
                    'campos': ['ejercicio', 'clave', 'descripcion'], 'descarga': None})
        return ctx


class DependenciaCreateView(LoginRequiredMixin, CreateView):
    model = Dependencia
    fields = ['ejercicio', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('dependencia_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Dependencia'
        ctx['back_url'] = reverse_lazy('dependencia_list')
        return ctx


class DependenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = Dependencia
    fields = ['ejercicio', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('dependencia_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Dependencia: {self.object.clave}'
        ctx['back_url'] = reverse_lazy('dependencia_list')
        return ctx


# ── Categorías ────────────────────────────────────────────────────────────────
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'catalogos/categoria_list.html'
    context_object_name = 'registros'
    paginate_by = 40

    def get_queryset(self):
        qs = Categoria.objects.all()
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        return qs.order_by('nivel', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Catálogo de Categorías'
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    fields = ['clave', 'subcategoria', 'descripcion', 'tipo_plaza', 'tp', 'nivel']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('categoria_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Categoría'
        ctx['back_url'] = reverse_lazy('categoria_list')
        return ctx


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    fields = ['clave', 'subcategoria', 'descripcion', 'tipo_plaza', 'tp', 'nivel']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('categoria_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Categoría: {self.object.clave}'
        ctx['back_url'] = reverse_lazy('categoria_list')
        return ctx


# ── Unidades Administrativas ──────────────────────────────────────────────────
class UnidadListView(LoginRequiredMixin, ListView):
    model = UnidadAdministrativa
    template_name = 'catalogos/unidad_list.html'
    context_object_name = 'registros'
    paginate_by = 40

    def get_queryset(self):
        qs = UnidadAdministrativa.objects.select_related('dependencia')
        q = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Unidades Administrativas'
        ctx['dependencias'] = Dependencia.objects.all().order_by('clave')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['dep_sel'] = self.request.GET.get('dep', '')
        return ctx


class UnidadCreateView(LoginRequiredMixin, CreateView):
    model = UnidadAdministrativa
    fields = ['ejercicio', 'dependencia', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('unidad_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Unidad Administrativa'
        ctx['back_url'] = reverse_lazy('unidad_list')
        return ctx


class UnidadUpdateView(LoginRequiredMixin, UpdateView):
    model = UnidadAdministrativa
    fields = ['ejercicio', 'dependencia', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('unidad_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Unidad: {self.object.clave}'
        ctx['back_url'] = reverse_lazy('unidad_list')
        return ctx


# ── Programas ─────────────────────────────────────────────────────────────────
class ProgramaListView(LoginRequiredMixin, ListView):
    model = Programa
    template_name = 'catalogos/programa_list.html'
    context_object_name = 'registros'
    paginate_by = 40

    def get_queryset(self):
        qs = Programa.objects.select_related('dependencia', 'unidad')
        q = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Programas Presupuestales'
        ctx['dependencias'] = Dependencia.objects.all().order_by('clave')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['dep_sel'] = self.request.GET.get('dep', '')
        return ctx


class ProgramaCreateView(LoginRequiredMixin, CreateView):
    model = Programa
    fields = ['ejercicio', 'dependencia', 'unidad', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('programa_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Programa'
        ctx['back_url'] = reverse_lazy('programa_list')
        return ctx


class ProgramaUpdateView(LoginRequiredMixin, UpdateView):
    model = Programa
    fields = ['ejercicio', 'dependencia', 'unidad', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('programa_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Programa: {self.object.clave}'
        ctx['back_url'] = reverse_lazy('programa_list')
        return ctx


# ── Proyectos ─────────────────────────────────────────────────────────────────
class ProyectoListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'catalogos/proyecto_list.html'
    context_object_name = 'registros'
    paginate_by = 40

    def get_queryset(self):
        qs = Proyecto.objects.select_related('dependencia', 'unidad', 'programa')
        q = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'programa__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Proyectos'
        ctx['dependencias'] = Dependencia.objects.all().order_by('clave')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['dep_sel'] = self.request.GET.get('dep', '')
        return ctx


class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    fields = ['ejercicio', 'dependencia', 'unidad', 'programa', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('proyecto_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Proyecto'
        ctx['back_url'] = reverse_lazy('proyecto_list')
        return ctx


class ProyectoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proyecto
    fields = ['ejercicio', 'dependencia', 'unidad', 'programa', 'clave', 'descripcion']
    template_name = 'catalogos/form_generica.html'
    success_url = reverse_lazy('proyecto_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Proyecto: {self.object.clave}'
        ctx['back_url'] = reverse_lazy('proyecto_list')
        return ctx


# ── Descarga de plantillas de catálogos ──────────────────────────────────────
@login_required
def descargar_catalogo(request, catalogo):
    nombres = {
        'categoria':  'Catalogo_Categoria.xlsx',
        'unidades':   'Catalogo_Unidades_Admvas.xlsx',
        'programas':  'Catalogo_Programas.xlsx',
        'proyectos':  'Catalogo_Proyectos.xlsx',
    }
    if catalogo not in nombres:
        raise Http404("Plantilla no encontrada.")

    nombre_archivo = nombres[catalogo]
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base, nombre_archivo)

    if not os.path.exists(ruta):
        raise Http404(f"El archivo {nombre_archivo} no está disponible.")

    response = FileResponse(
        open(ruta, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response
