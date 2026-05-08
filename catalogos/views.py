# -*- coding: utf-8 -*-
import os
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from django.db.models import Q

from .models import (
    FuenteFinanciamiento, Dependencia, UnidadAdministrativa,
    Programa, Proyecto, Categoria, TipoContratacion, TipoPersonal,
    TipoFuncion, NivelEstructura, EstatusPlaza, CentroTrabajo,
    TipoDeclaracion, Area, NivelEscolaridad, Discapacidad,
    EnfermedadCronica, Pueblo, MotivoBaja, Idioma, EstadoCivil,
    Pais, EntidadFederativa, Municipio, Sindicato, Inmueble,
)
from .forms import (
    FuenteFinanciamientoForm, DependenciaForm, UnidadAdministrativaForm,
    ProgramaForm, ProyectoForm, CategoriaForm, TipoContratacionForm,
    TipoPersonalForm, TipoFuncionForm, NivelEstructuraForm, EstatusPlazaForm,
    CentroTrabajoForm, TipoDeclaracionForm, AreaForm, NivelEscolaridadForm,
    DiscapacidadForm, EnfermedadCronicaForm, PuebloForm, MotivoBajaForm,
    IdiomaForm, EstadoCivilForm, PaisForm, EntidadFederativaForm,
    MunicipioForm, SindicatoForm, InmuebleForm,
)

# ── Índice ────────────────────────────────────────────────────────────────────
def catalogo_index(request):
    grupos = [
        {
            'nombre': 'Estructura Presupuestal',
            'color':  'verde',
            'items': [
                {'nombre': 'Fuentes de Financiamiento', 'url': 'fuente_list',    'icono': '💰', 'descarga': None},
                {'nombre': 'Dependencias',               'url': 'dependencia_list','icono': '🏛️', 'descarga': None},
                {'nombre': 'Unidades Administrativas',   'url': 'unidad_list',   'icono': '🏢', 'descarga': 'unidades'},
                {'nombre': 'Programas',                  'url': 'programa_list', 'icono': '📋', 'descarga': 'programas'},
                {'nombre': 'Proyectos',                  'url': 'proyecto_list', 'icono': '📁', 'descarga': 'proyectos'},
            ]
        },
        {
            'nombre': 'Puestos y Plazas',
            'color':  'azul',
            'items': [
                {'nombre': 'Categorías',          'url': 'categoria_list',       'icono': '🏷️',  'descarga': 'categoria'},
                {'nombre': 'Tipos de Contratación','url': 'tipo_contratacion_list','icono': '📝', 'descarga': None},
                {'nombre': 'Tipos de Personal',   'url': 'tipo_personal_list',   'icono': '👤',  'descarga': None},
                {'nombre': 'Tipos de Función',    'url': 'tipo_funcion_list',    'icono': '⚙️',  'descarga': None},
                {'nombre': 'Niveles de Estructura','url': 'nivel_estructura_list','icono': '🔢',  'descarga': None},
                {'nombre': 'Estatus de Plaza',    'url': 'estatus_plaza_list',   'icono': '📊',  'descarga': None},
                {'nombre': 'Centros de Trabajo',  'url': 'centro_trabajo_list',  'icono': '🏫',  'descarga': None},
            ]
        },
        {
            'nombre': 'Datos del Servidor Público',
            'color':  'dorado',
            'items': [
                {'nombre': 'Estados Civiles',         'url': 'estado_civil_list',     'icono': '💍', 'descarga': None},
                {'nombre': 'Entidades Federativas',   'url': 'entidad_list',          'icono': '🗺️', 'descarga': None},
                {'nombre': 'Municipios',              'url': 'municipio_list',        'icono': '📍', 'descarga': None},
                {'nombre': 'Países',                  'url': 'pais_list',             'icono': '🌎', 'descarga': None},
                {'nombre': 'Sindicatos',              'url': 'sindicato_list',        'icono': '🤝', 'descarga': None},
                {'nombre': 'Niveles de Escolaridad',  'url': 'nivel_escolaridad_list','icono': '🎓', 'descarga': None},
                {'nombre': 'Idiomas / Lenguas',       'url': 'idioma_list',           'icono': '🗣️', 'descarga': None},
                {'nombre': 'Discapacidades',          'url': 'discapacidad_list',     'icono': '♿', 'descarga': None},
                {'nombre': 'Enfermedades Crónicas',   'url': 'enfermedad_list',       'icono': '🏥', 'descarga': None},
                {'nombre': 'Pueblos Indígenas',       'url': 'pueblo_list',           'icono': '🪶', 'descarga': None},
            ]
        },
        {
            'nombre': 'Otros Catálogos',
            'color':  'rojo',
            'items': [
                {'nombre': 'Tipos de Declaración',  'url': 'tipo_declaracion_list', 'icono': '⚖️', 'descarga': None},
                {'nombre': 'Áreas',                 'url': 'area_list',             'icono': '🏗️', 'descarga': None},
                {'nombre': 'Motivos de Baja',       'url': 'motivo_baja_list',      'icono': '🚫', 'descarga': None},
                {'nombre': 'Inmuebles',             'url': 'inmueble_list',         'icono': '🏠', 'descarga': None},
            ]
        },
    ]
    return render(request, 'catalogos/index.html', {
        'titulo': 'Catálogos del Sistema',
        'grupos': grupos,
    })


# ── Mixin reutilizable ────────────────────────────────────────────────────────
class CatalogoMixin(LoginRequiredMixin):
    """Mixin base para vistas de catálogos: agrega titulo y back_url al contexto."""
    titulo       = ''
    back_url_name = ''

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo']   = self.titulo
        ctx['back_url'] = reverse_lazy(self.back_url_name) if self.back_url_name else '#'
        return ctx


def make_list_view(model, template, titulo, search_fields=None, paginate=30, extra_ctx=None):
    """Factoría de ListViews para catálogos simples."""
    class V(LoginRequiredMixin, ListView):
        queryset         = model.objects.all()
        template_name    = template
        context_object_name = 'registros'
        paginate_by      = paginate

        def get_queryset(self):
            qs = super().get_queryset()
            q  = self.request.GET.get('q', '')
            if q and search_fields:
                filtro = Q()
                for f in search_fields:
                    filtro |= Q(**{f'{f}__icontains': q})
                qs = qs.filter(filtro)
            return qs

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['titulo'] = titulo
            ctx['q']      = self.request.GET.get('q', '')
            if extra_ctx:
                ctx.update(extra_ctx() if callable(extra_ctx) else extra_ctx)
            return ctx
    return V


def make_create_view(model, form_class, success_url, titulo, back_url, template='catalogos/form_generica.html'):
    class V(CatalogoMixin, CreateView):
        pass
    V.model        = model
    V.form_class   = form_class
    V.template_name      = template
    V.success_url        = reverse_lazy(success_url)
    V.titulo             = titulo
    V.back_url_name      = back_url
    return V


def make_update_view(model, form_class, success_url, titulo_prefix, back_url, template='catalogos/form_generica.html'):
    class V(LoginRequiredMixin, UpdateView):
        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['titulo']   = f'{titulo_prefix}: {self.object}'
            ctx['back_url'] = reverse_lazy(back_url)
            return ctx
    V.model        = model
    V.form_class   = form_class
    V.template_name      = template
    V.success_url        = reverse_lazy(success_url)
    return V


# ── Fuente de Financiamiento ──────────────────────────────────────────────────
FuenteListView   = make_list_view(FuenteFinanciamiento, 'catalogos/simple_list.html',
                                  'Fuentes de Financiamiento', ['clave', 'descripcion'])
FuenteCreateView = make_create_view(FuenteFinanciamiento, FuenteFinanciamientoForm,
                                    'fuente_list', 'Nueva Fuente de Financiamiento', 'fuente_list')
FuenteUpdateView = make_update_view(FuenteFinanciamiento, FuenteFinanciamientoForm,
                                    'fuente_list', 'Editar Fuente', 'fuente_list')

# ── Dependencias ──────────────────────────────────────────────────────────────
DependenciaListView   = make_list_view(Dependencia, 'catalogos/simple_list.html',
                                       'Dependencias', ['clave', 'descripcion'])
DependenciaCreateView = make_create_view(Dependencia, DependenciaForm,
                                         'dependencia_list', 'Nueva Dependencia', 'dependencia_list')
DependenciaUpdateView = make_update_view(Dependencia, DependenciaForm,
                                         'dependencia_list', 'Editar Dependencia', 'dependencia_list')

# ── Unidades Administrativas ──────────────────────────────────────────────────
class UnidadListView(LoginRequiredMixin, ListView):
    model               = UnidadAdministrativa
    template_name       = 'catalogos/unidad_list.html'
    context_object_name = 'registros'
    paginate_by         = 40

    def get_queryset(self):
        qs  = UnidadAdministrativa.objects.select_related('dependencia')
        q   = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Unidades Administrativas',
                    'dependencias': Dependencia.objects.all().order_by('clave'),
                    'q': self.request.GET.get('q', ''),
                    'dep_sel': self.request.GET.get('dep', '')})
        return ctx

UnidadCreateView = make_create_view(UnidadAdministrativa, UnidadAdministrativaForm,
                                    'unidad_list', 'Nueva Unidad Administrativa', 'unidad_list')
UnidadUpdateView = make_update_view(UnidadAdministrativa, UnidadAdministrativaForm,
                                    'unidad_list', 'Editar Unidad', 'unidad_list')

# ── Programas ─────────────────────────────────────────────────────────────────
class ProgramaListView(LoginRequiredMixin, ListView):
    model               = Programa
    template_name       = 'catalogos/programa_list.html'
    context_object_name = 'registros'
    paginate_by         = 40

    def get_queryset(self):
        qs  = Programa.objects.select_related('dependencia', 'unidad')
        q   = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Programas Presupuestales',
                    'dependencias': Dependencia.objects.all().order_by('clave'),
                    'q': self.request.GET.get('q', ''),
                    'dep_sel': self.request.GET.get('dep', '')})
        return ctx

ProgramaCreateView = make_create_view(Programa, ProgramaForm,
                                      'programa_list', 'Nuevo Programa', 'programa_list')
ProgramaUpdateView = make_update_view(Programa, ProgramaForm,
                                      'programa_list', 'Editar Programa', 'programa_list')

# ── Proyectos ─────────────────────────────────────────────────────────────────
class ProyectoListView(LoginRequiredMixin, ListView):
    model               = Proyecto
    template_name       = 'catalogos/proyecto_list.html'
    context_object_name = 'registros'
    paginate_by         = 40

    def get_queryset(self):
        qs  = Proyecto.objects.select_related('dependencia', 'unidad', 'programa')
        q   = self.request.GET.get('q', '')
        dep = self.request.GET.get('dep', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if dep:
            qs = qs.filter(dependencia_id=dep)
        return qs.order_by('dependencia__clave', 'programa__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Proyectos',
                    'dependencias': Dependencia.objects.all().order_by('clave'),
                    'q': self.request.GET.get('q', ''),
                    'dep_sel': self.request.GET.get('dep', '')})
        return ctx

ProyectoCreateView = make_create_view(Proyecto, ProyectoForm,
                                      'proyecto_list', 'Nuevo Proyecto', 'proyecto_list')
ProyectoUpdateView = make_update_view(Proyecto, ProyectoForm,
                                      'proyecto_list', 'Editar Proyecto', 'proyecto_list')

# ── Categorías ────────────────────────────────────────────────────────────────
class CategoriaListView(LoginRequiredMixin, ListView):
    model               = Categoria
    template_name       = 'catalogos/categoria_list.html'
    context_object_name = 'registros'
    paginate_by         = 40

    def get_queryset(self):
        qs = Categoria.objects.all()
        q  = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        return qs.order_by('nivel', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Categorías', 'q': self.request.GET.get('q', '')})
        return ctx

CategoriaCreateView = make_create_view(Categoria, CategoriaForm,
                                       'categoria_list', 'Nueva Categoría', 'categoria_list')
CategoriaUpdateView = make_update_view(Categoria, CategoriaForm,
                                       'categoria_list', 'Editar Categoría', 'categoria_list')

# ── Catálogos simples (clave + descripcion) ───────────────────────────────────
TipoContratacionListView   = make_list_view(TipoContratacion,  'catalogos/simple_list.html', 'Tipos de Contratación',  ['clave','descripcion'])
TipoContratacionCreateView = make_create_view(TipoContratacion,  TipoContratacionForm,  'tipo_contratacion_list', 'Nuevo Tipo Contratación',  'tipo_contratacion_list')
TipoContratacionUpdateView = make_update_view(TipoContratacion,  TipoContratacionForm,  'tipo_contratacion_list', 'Editar',                    'tipo_contratacion_list')

TipoPersonalListView   = make_list_view(TipoPersonal,    'catalogos/simple_list.html', 'Tipos de Personal',      ['clave','descripcion'])
TipoPersonalCreateView = make_create_view(TipoPersonal,    TipoPersonalForm,    'tipo_personal_list',    'Nuevo Tipo Personal',       'tipo_personal_list')
TipoPersonalUpdateView = make_update_view(TipoPersonal,    TipoPersonalForm,    'tipo_personal_list',    'Editar',                    'tipo_personal_list')

TipoFuncionListView   = make_list_view(TipoFuncion,     'catalogos/simple_list.html', 'Tipos de Función',       ['clave','descripcion'])
TipoFuncionCreateView = make_create_view(TipoFuncion,     TipoFuncionForm,     'tipo_funcion_list',     'Nuevo Tipo Función',         'tipo_funcion_list')
TipoFuncionUpdateView = make_update_view(TipoFuncion,     TipoFuncionForm,     'tipo_funcion_list',     'Editar',                    'tipo_funcion_list')

NivelEstructuraListView   = make_list_view(NivelEstructura,  'catalogos/simple_list.html', 'Niveles de Estructura',  ['clave','descripcion'])
NivelEstructuraCreateView = make_create_view(NivelEstructura,  NivelEstructuraForm,  'nivel_estructura_list', 'Nuevo Nivel',               'nivel_estructura_list')
NivelEstructuraUpdateView = make_update_view(NivelEstructura,  NivelEstructuraForm,  'nivel_estructura_list', 'Editar',                    'nivel_estructura_list')

EstatusPlazaListView   = make_list_view(EstatusPlaza,    'catalogos/simple_list.html', 'Estatus de Plaza',       ['clave','descripcion'])
EstatusPlazaCreateView = make_create_view(EstatusPlaza,    EstatusPlazaForm,    'estatus_plaza_list',    'Nuevo Estatus',              'estatus_plaza_list')
EstatusPlazaUpdateView = make_update_view(EstatusPlaza,    EstatusPlazaForm,    'estatus_plaza_list',    'Editar',                    'estatus_plaza_list')

CentroTrabajoListView   = make_list_view(CentroTrabajo,   'catalogos/simple_list.html', 'Centros de Trabajo',     ['clave','nombre'])
CentroTrabajoCreateView = make_create_view(CentroTrabajo,   CentroTrabajoForm,   'centro_trabajo_list',   'Nuevo Centro de Trabajo',   'centro_trabajo_list')
CentroTrabajoUpdateView = make_update_view(CentroTrabajo,   CentroTrabajoForm,   'centro_trabajo_list',   'Editar',                    'centro_trabajo_list')

TipoDeclaracionListView   = make_list_view(TipoDeclaracion, 'catalogos/simple_list.html', 'Tipos de Declaración',  ['clave','descripcion'])
TipoDeclaracionCreateView = make_create_view(TipoDeclaracion, TipoDeclaracionForm, 'tipo_declaracion_list', 'Nuevo Tipo Declaración',    'tipo_declaracion_list')
TipoDeclaracionUpdateView = make_update_view(TipoDeclaracion, TipoDeclaracionForm, 'tipo_declaracion_list', 'Editar',                    'tipo_declaracion_list')

AreaListView   = make_list_view(Area,          'catalogos/simple_list.html', 'Áreas',                  ['clave','descripcion'])
AreaCreateView = make_create_view(Area,          AreaForm,          'area_list',             'Nueva Área',                'area_list')
AreaUpdateView = make_update_view(Area,          AreaForm,          'area_list',             'Editar',                    'area_list')

NivelEscolaridadListView   = make_list_view(NivelEscolaridad, 'catalogos/simple_list.html', 'Niveles de Escolaridad', ['descripcion','estatus'])
NivelEscolaridadCreateView = make_create_view(NivelEscolaridad, NivelEscolaridadForm, 'nivel_escolaridad_list', 'Nuevo Nivel Escolaridad', 'nivel_escolaridad_list')
NivelEscolaridadUpdateView = make_update_view(NivelEscolaridad, NivelEscolaridadForm, 'nivel_escolaridad_list', 'Editar',                  'nivel_escolaridad_list')

DiscapacidadListView   = make_list_view(Discapacidad,   'catalogos/simple_list.html', 'Discapacidades',         ['tipo','descripcion'])
DiscapacidadCreateView = make_create_view(Discapacidad,   DiscapacidadForm,   'discapacidad_list',     'Nueva Discapacidad',         'discapacidad_list')
DiscapacidadUpdateView = make_update_view(Discapacidad,   DiscapacidadForm,   'discapacidad_list',     'Editar',                    'discapacidad_list')

EnfermedadListView   = make_list_view(EnfermedadCronica,'catalogos/simple_list.html', 'Enfermedades Crónicas',  ['descripcion'])
EnfermedadCreateView = make_create_view(EnfermedadCronica,EnfermedadCronicaForm,'enfermedad_list',       'Nueva Enfermedad',           'enfermedad_list')
EnfermedadUpdateView = make_update_view(EnfermedadCronica,EnfermedadCronicaForm,'enfermedad_list',       'Editar',                    'enfermedad_list')

PuebloListView   = make_list_view(Pueblo,        'catalogos/simple_list.html', 'Pueblos Indígenas',      ['descripcion'])
PuebloCreateView = make_create_view(Pueblo,        PuebloForm,        'pueblo_list',           'Nuevo Pueblo',               'pueblo_list')
PuebloUpdateView = make_update_view(Pueblo,        PuebloForm,        'pueblo_list',           'Editar',                    'pueblo_list')

MotivoBajaListView   = make_list_view(MotivoBaja,    'catalogos/simple_list.html', 'Motivos de Baja',        ['clave','descripcion'])
MotivoBajaCreateView = make_create_view(MotivoBaja,    MotivoBajaForm,    'motivo_baja_list',      'Nuevo Motivo de Baja',       'motivo_baja_list')
MotivoBajaUpdateView = make_update_view(MotivoBaja,    MotivoBajaForm,    'motivo_baja_list',      'Editar',                    'motivo_baja_list')

IdiomaListView   = make_list_view(Idioma,        'catalogos/simple_list.html', 'Idiomas / Lenguas',      ['descripcion','familia_linguistica'])
IdiomaCreateView = make_create_view(Idioma,        IdiomaForm,        'idioma_list',           'Nuevo Idioma / Lengua',      'idioma_list')
IdiomaUpdateView = make_update_view(Idioma,        IdiomaForm,        'idioma_list',           'Editar',                    'idioma_list')

EstadoCivilListView   = make_list_view(EstadoCivil,   'catalogos/simple_list.html', 'Estados Civiles',        ['clave','descripcion'])
EstadoCivilCreateView = make_create_view(EstadoCivil,   EstadoCivilForm,   'estado_civil_list',     'Nuevo Estado Civil',         'estado_civil_list')
EstadoCivilUpdateView = make_update_view(EstadoCivil,   EstadoCivilForm,   'estado_civil_list',     'Editar',                    'estado_civil_list')

PaisListView   = make_list_view(Pais,          'catalogos/simple_list.html', 'Países',                 ['nombre'])
PaisCreateView = make_create_view(Pais,          PaisForm,          'pais_list',             'Nuevo País',                'pais_list')
PaisUpdateView = make_update_view(Pais,          PaisForm,          'pais_list',             'Editar',                    'pais_list')

EntidadListView   = make_list_view(EntidadFederativa,'catalogos/simple_list.html', 'Entidades Federativas',  ['nombre','abreviatura'])
EntidadCreateView = make_create_view(EntidadFederativa,EntidadFederativaForm,'entidad_list',          'Nueva Entidad Federativa',   'entidad_list')
EntidadUpdateView = make_update_view(EntidadFederativa,EntidadFederativaForm,'entidad_list',          'Editar',                    'entidad_list')

class MunicipioListView(LoginRequiredMixin, ListView):
    model               = Municipio
    template_name       = 'catalogos/simple_list.html'
    context_object_name = 'registros'
    paginate_by         = 50

    def get_queryset(self):
        qs  = Municipio.objects.select_related('entidad')
        q   = self.request.GET.get('q', '')
        ent = self.request.GET.get('ent', '')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(clave__icontains=q))
        if ent:
            qs = qs.filter(entidad_id=ent)
        return qs.order_by('entidad__nombre', 'nombre')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Municipios', 'q': self.request.GET.get('q', ''),
                    'entidades': EntidadFederativa.objects.all().order_by('nombre'),
                    'ent_sel': self.request.GET.get('ent', '')})
        return ctx

MunicipioCreateView = make_create_view(Municipio, MunicipioForm, 'municipio_list', 'Nuevo Municipio', 'municipio_list')
MunicipioUpdateView = make_update_view(Municipio, MunicipioForm, 'municipio_list', 'Editar Municipio', 'municipio_list')

SindicatoListView   = make_list_view(Sindicato,    'catalogos/simple_list.html', 'Sindicatos',             ['clave','descripcion'])
SindicatoCreateView = make_create_view(Sindicato,    SindicatoForm,    'sindicato_list',        'Nuevo Sindicato',            'sindicato_list')
SindicatoUpdateView = make_update_view(Sindicato,    SindicatoForm,    'sindicato_list',        'Editar',                    'sindicato_list')

class InmuebleListView(LoginRequiredMixin, ListView):
    model               = Inmueble
    template_name       = 'catalogos/simple_list.html'
    context_object_name = 'registros'
    paginate_by         = 30

    def get_queryset(self):
        qs  = Inmueble.objects.select_related('dependencia')
        q   = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        return qs.order_by('dependencia__clave', 'clave')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'titulo': 'Inmuebles', 'q': self.request.GET.get('q', '')})
        return ctx

InmuebleCreateView = make_create_view(Inmueble, InmuebleForm, 'inmueble_list', 'Nuevo Inmueble', 'inmueble_list')
InmuebleUpdateView = make_update_view(Inmueble, InmuebleForm, 'inmueble_list', 'Editar Inmueble', 'inmueble_list')


# ── Descarga de plantillas ────────────────────────────────────────────────────
@login_required
def descargar_catalogo(request, catalogo):
    nombres = {
        'categoria': 'Catalogo_Categoria.xlsx',
        'unidades':  'Catalogo_Unidades_Admvas.xlsx',
        'programas': 'Catalogo_Programas.xlsx',
        'proyectos': 'Catalogo_Proyectos.xlsx',
    }
    if catalogo not in nombres:
        raise Http404("Plantilla no encontrada.")
    nombre_archivo = nombres[catalogo]
    base  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta  = os.path.join(base, nombre_archivo)
    if not os.path.exists(ruta):
        raise Http404(f"El archivo {nombre_archivo} no está disponible.")
    response = FileResponse(
        open(ruta, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response
