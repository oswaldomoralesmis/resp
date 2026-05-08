# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo_index, name='catalogo_index'),
    # Fuentes de Financiamiento
    path('fuentes/',                    views.FuenteListView.as_view(),           name='fuente_list'),
    path('fuentes/nueva/',              views.FuenteCreateView.as_view(),         name='fuente_create'),
    path('fuentes/<int:pk>/editar/',    views.FuenteUpdateView.as_view(),         name='fuente_update'),
    # Dependencias
    path('dependencias/',               views.DependenciaListView.as_view(),      name='dependencia_list'),
    path('dependencias/nueva/',         views.DependenciaCreateView.as_view(),    name='dependencia_create'),
    path('dependencias/<int:pk>/editar/',views.DependenciaUpdateView.as_view(),   name='dependencia_update'),
    # Unidades Administrativas
    path('unidades/',                   views.UnidadListView.as_view(),           name='unidad_list'),
    path('unidades/nueva/',             views.UnidadCreateView.as_view(),         name='unidad_create'),
    path('unidades/<int:pk>/editar/',   views.UnidadUpdateView.as_view(),         name='unidad_update'),
    # Programas
    path('programas/',                  views.ProgramaListView.as_view(),         name='programa_list'),
    path('programas/nuevo/',            views.ProgramaCreateView.as_view(),       name='programa_create'),
    path('programas/<int:pk>/editar/',  views.ProgramaUpdateView.as_view(),       name='programa_update'),
    # Proyectos
    path('proyectos/',                  views.ProyectoListView.as_view(),         name='proyecto_list'),
    path('proyectos/nuevo/',            views.ProyectoCreateView.as_view(),       name='proyecto_create'),
    path('proyectos/<int:pk>/editar/',  views.ProyectoUpdateView.as_view(),       name='proyecto_update'),
    # Categorías
    path('categorias/',                 views.CategoriaListView.as_view(),        name='categoria_list'),
    path('categorias/nueva/',           views.CategoriaCreateView.as_view(),      name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(),      name='categoria_update'),
    # Tipos de Contratación
    path('tipo-contratacion/',               views.TipoContratacionListView.as_view(),   name='tipo_contratacion_list'),
    path('tipo-contratacion/nuevo/',         views.TipoContratacionCreateView.as_view(), name='tipo_contratacion_create'),
    path('tipo-contratacion/<int:pk>/editar/',views.TipoContratacionUpdateView.as_view(),name='tipo_contratacion_update'),
    # Tipos de Personal
    path('tipo-personal/',               views.TipoPersonalListView.as_view(),    name='tipo_personal_list'),
    path('tipo-personal/nuevo/',         views.TipoPersonalCreateView.as_view(),  name='tipo_personal_create'),
    path('tipo-personal/<int:pk>/editar/',views.TipoPersonalUpdateView.as_view(), name='tipo_personal_update'),
    # Tipos de Función
    path('tipo-funcion/',               views.TipoFuncionListView.as_view(),      name='tipo_funcion_list'),
    path('tipo-funcion/nuevo/',         views.TipoFuncionCreateView.as_view(),    name='tipo_funcion_create'),
    path('tipo-funcion/<int:pk>/editar/',views.TipoFuncionUpdateView.as_view(),   name='tipo_funcion_update'),
    # Niveles de Estructura
    path('nivel-estructura/',               views.NivelEstructuraListView.as_view(),   name='nivel_estructura_list'),
    path('nivel-estructura/nuevo/',         views.NivelEstructuraCreateView.as_view(), name='nivel_estructura_create'),
    path('nivel-estructura/<int:pk>/editar/',views.NivelEstructuraUpdateView.as_view(),name='nivel_estructura_update'),
    # Estatus de Plaza
    path('estatus-plaza/',               views.EstatusPlazaListView.as_view(),    name='estatus_plaza_list'),
    path('estatus-plaza/nuevo/',         views.EstatusPlazaCreateView.as_view(),  name='estatus_plaza_create'),
    path('estatus-plaza/<int:pk>/editar/',views.EstatusPlazaUpdateView.as_view(), name='estatus_plaza_update'),
    # Centros de Trabajo
    path('centros-trabajo/',               views.CentroTrabajoListView.as_view(),   name='centro_trabajo_list'),
    path('centros-trabajo/nuevo/',         views.CentroTrabajoCreateView.as_view(), name='centro_trabajo_create'),
    path('centros-trabajo/<int:pk>/editar/',views.CentroTrabajoUpdateView.as_view(),name='centro_trabajo_update'),
    # Tipos de Declaración
    path('tipo-declaracion/',               views.TipoDeclaracionListView.as_view(),   name='tipo_declaracion_list'),
    path('tipo-declaracion/nuevo/',         views.TipoDeclaracionCreateView.as_view(), name='tipo_declaracion_create'),
    path('tipo-declaracion/<int:pk>/editar/',views.TipoDeclaracionUpdateView.as_view(),name='tipo_declaracion_update'),
    # Áreas
    path('areas/',               views.AreaListView.as_view(),    name='area_list'),
    path('areas/nueva/',         views.AreaCreateView.as_view(),  name='area_create'),
    path('areas/<int:pk>/editar/',views.AreaUpdateView.as_view(), name='area_update'),
    # Niveles de Escolaridad
    path('nivel-escolaridad/',               views.NivelEscolaridadListView.as_view(),   name='nivel_escolaridad_list'),
    path('nivel-escolaridad/nuevo/',         views.NivelEscolaridadCreateView.as_view(), name='nivel_escolaridad_create'),
    path('nivel-escolaridad/<int:pk>/editar/',views.NivelEscolaridadUpdateView.as_view(),name='nivel_escolaridad_update'),
    # Discapacidades
    path('discapacidades/',               views.DiscapacidadListView.as_view(),   name='discapacidad_list'),
    path('discapacidades/nueva/',         views.DiscapacidadCreateView.as_view(), name='discapacidad_create'),
    path('discapacidades/<int:pk>/editar/',views.DiscapacidadUpdateView.as_view(),name='discapacidad_update'),
    # Enfermedades Crónicas
    path('enfermedades/',               views.EnfermedadListView.as_view(),   name='enfermedad_list'),
    path('enfermedades/nueva/',         views.EnfermedadCreateView.as_view(), name='enfermedad_create'),
    path('enfermedades/<int:pk>/editar/',views.EnfermedadUpdateView.as_view(),name='enfermedad_update'),
    # Pueblos
    path('pueblos/',               views.PuebloListView.as_view(),   name='pueblo_list'),
    path('pueblos/nuevo/',         views.PuebloCreateView.as_view(), name='pueblo_create'),
    path('pueblos/<int:pk>/editar/',views.PuebloUpdateView.as_view(),name='pueblo_update'),
    # Motivos de Baja
    path('motivos-baja/',               views.MotivoBajaListView.as_view(),   name='motivo_baja_list'),
    path('motivos-baja/nuevo/',         views.MotivoBajaCreateView.as_view(), name='motivo_baja_create'),
    path('motivos-baja/<int:pk>/editar/',views.MotivoBajaUpdateView.as_view(),name='motivo_baja_update'),
    # Idiomas
    path('idiomas/',               views.IdiomaListView.as_view(),   name='idioma_list'),
    path('idiomas/nuevo/',         views.IdiomaCreateView.as_view(), name='idioma_create'),
    path('idiomas/<int:pk>/editar/',views.IdiomaUpdateView.as_view(),name='idioma_update'),
    # Estados Civiles
    path('estados-civiles/',               views.EstadoCivilListView.as_view(),   name='estado_civil_list'),
    path('estados-civiles/nuevo/',         views.EstadoCivilCreateView.as_view(), name='estado_civil_create'),
    path('estados-civiles/<int:pk>/editar/',views.EstadoCivilUpdateView.as_view(),name='estado_civil_update'),
    # Países
    path('paises/',               views.PaisListView.as_view(),   name='pais_list'),
    path('paises/nuevo/',         views.PaisCreateView.as_view(), name='pais_create'),
    path('paises/<int:pk>/editar/',views.PaisUpdateView.as_view(),name='pais_update'),
    # Entidades Federativas
    path('entidades/',               views.EntidadListView.as_view(),   name='entidad_list'),
    path('entidades/nueva/',         views.EntidadCreateView.as_view(), name='entidad_create'),
    path('entidades/<int:pk>/editar/',views.EntidadUpdateView.as_view(),name='entidad_update'),
    # Municipios
    path('municipios/',               views.MunicipioListView.as_view(),   name='municipio_list'),
    path('municipios/nuevo/',         views.MunicipioCreateView.as_view(), name='municipio_create'),
    path('municipios/<int:pk>/editar/',views.MunicipioUpdateView.as_view(),name='municipio_update'),
    # Sindicatos
    path('sindicatos/',               views.SindicatoListView.as_view(),   name='sindicato_list'),
    path('sindicatos/nuevo/',         views.SindicatoCreateView.as_view(), name='sindicato_create'),
    path('sindicatos/<int:pk>/editar/',views.SindicatoUpdateView.as_view(),name='sindicato_update'),
    # Inmuebles
    path('inmuebles/',               views.InmuebleListView.as_view(),   name='inmueble_list'),
    path('inmuebles/nuevo/',         views.InmuebleCreateView.as_view(), name='inmueble_create'),
    path('inmuebles/<int:pk>/editar/',views.InmuebleUpdateView.as_view(),name='inmueble_update'),
    # Descarga plantillas
    path('descargar/<str:catalogo>/', views.descargar_catalogo, name='descargar_catalogo'),
]
