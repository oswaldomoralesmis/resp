# -*- coding: utf-8 -*-
"""Config declarativa de exportación 'todos los registros' a Excel para cada
catálogo (botón 'Exportar Excel' en cada lista, igual que en Plazas). Cada
entrada define el modelo, el título de la hoja, las columnas (encabezado +
función para extraer el valor de cada registro) y, si aplica, el filtro por
dependencia del usuario."""
from .models import (
    FuenteFinanciamiento, Dependencia, UnidadAdministrativa, Programa, Proyecto,
    Categoria, TipoContratacion, TipoPersonal, TipoFuncion, NivelEstructura,
    EstatusPlaza, CentroTrabajo, TipoDeclaracion, Area, NivelEscolaridad,
    Discapacidad, EnfermedadCronica, Pueblo, MotivoBaja, Idioma, EstadoCivil,
    Pais, EntidadFederativa, Municipio, Sindicato, Inmueble,
)

def _filas_proyecto(qs):
    """Un Proyecto puede tener varios programas/unidades (M2M); la plantilla
    de importación espera una fila por cada combinación proyecto-programa,
    repitiendo la CLAVE_PROYECTO — igual que Catalogo_Proyectos.xlsx. Si un
    proyecto no tiene ningún programa asignado (caso raro), igual se exporta
    una fila con ID_UNIDAD/ID_PROGRAMA vacíos, para no perderlo de vista."""
    for p in qs:
        dep_clave = p.dependencia.clave if p.dependencia else ''
        programas = sorted(p.programas.all(), key=lambda prg: prg.clave)
        if not programas:
            yield [f'{dep_clave}-{p.clave}'.strip('-'), dep_clave, '', '', p.clave, p.descripcion]
            continue
        for prg in programas:
            uni_clave = prg.unidad.clave if prg.unidad else ''
            llave = '-'.join(filter(None, [dep_clave, uni_clave, prg.clave, p.clave]))
            yield [llave, dep_clave, uni_clave, prg.clave, p.clave, p.descripcion]


CATALOGOS_EXPORT = {
    'fuente': {
        'model': FuenteFinanciamiento, 'titulo': 'Fuentes de Financiamiento',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'dependencia': {
        'model': Dependencia, 'titulo': 'Dependencias',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'dependencia_lookup': 'pk', 'order_by': ['clave'],
    },
    'unidad': {
        'model': UnidadAdministrativa, 'titulo': 'Unidades Administrativas',
        'select_related': ['dependencia'],
        'columnas': [
            ('Dependencia', lambda o: o.dependencia.clave),
            ('Clave', lambda o: o.clave),
            ('Descripción', lambda o: o.descripcion),
        ],
        'dependencia_lookup': 'dependencia', 'order_by': ['dependencia__clave', 'clave'],
    },
    'programa': {
        'model': Programa, 'titulo': 'Programas',
        'select_related': ['dependencia', 'unidad'],
        'columnas': [
            ('Dependencia', lambda o: o.dependencia.clave),
            ('Unidad', lambda o: o.unidad.clave),
            ('Clave', lambda o: o.clave),
            ('Descripción', lambda o: o.descripcion),
        ],
        'dependencia_lookup': 'dependencia', 'order_by': ['dependencia__clave', 'clave'],
    },
    'proyecto': {
        'model': Proyecto, 'titulo': 'Proyectos',
        'select_related': ['dependencia'],
        'prefetch_related': ['programas__unidad'],
        # Mismas 6 columnas y mismo orden que Catalogo_Proyectos.xlsx (la
        # plantilla de importación), para poder editar el export y volver a
        # subirlo tal cual. LLAVE es informativa (importar_proyectos no la
        # lee, igual que en la plantilla real) — solo ayuda a ubicar la fila.
        'columnas': [
            ('LLAVE', None), ('ID_DEPCIA', None), ('ID_UNIDAD', None),
            ('ID_PROGRAMA', None), ('CLAVE_PROYECTO', None), ('DESCRIPCION DEL PROYECTO', None),
        ],
        'filas': _filas_proyecto,
        'dependencia_lookup': 'dependencia', 'order_by': ['dependencia__clave', 'clave'],
    },
    'categoria': {
        'model': Categoria, 'titulo': 'Categorías',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Subcategoría', lambda o: o.subcategoria),
            ('Descripción', lambda o: o.descripcion),
            ('Tipo Plaza', lambda o: o.tipo_plaza),
            ('TP', lambda o: o.tp),
            ('Nivel', lambda o: o.nivel),
        ],
        'order_by': ['nivel', 'clave'],
    },
    'tipo_contratacion': {
        'model': TipoContratacion, 'titulo': 'Tipos de Contratación',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'tipo_personal': {
        'model': TipoPersonal, 'titulo': 'Tipos de Personal',
        'select_related': ['tipo_contratacion'],
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Tipo Contratación', lambda o: o.tipo_contratacion.clave if o.tipo_contratacion else ''),
            ('Descripción', lambda o: o.descripcion),
        ],
        'order_by': ['clave'],
    },
    'tipo_funcion': {
        'model': TipoFuncion, 'titulo': 'Tipos de Función',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'nivel_estructura': {
        'model': NivelEstructura, 'titulo': 'Niveles de Estructura',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Descripción', lambda o: o.descripcion),
            ('Nivel', lambda o: o.nivel),
        ],
        'order_by': ['nivel'],
    },
    'estatus_plaza': {
        'model': EstatusPlaza, 'titulo': 'Estatus de Plaza',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'centro_trabajo': {
        'model': CentroTrabajo, 'titulo': 'Centros de Trabajo',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Nombre', lambda o: o.nombre),
            ('Nivel Educativo', lambda o: o.nivel_educativo),
            ('Municipio', lambda o: o.municipio),
            ('Domicilio', lambda o: o.domicilio),
        ],
        'order_by': ['clave'],
    },
    'tipo_declaracion': {
        'model': TipoDeclaracion, 'titulo': 'Tipos de Declaración',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'area': {
        'model': Area, 'titulo': 'Áreas',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'nivel_escolaridad': {
        'model': NivelEscolaridad, 'titulo': 'Niveles de Escolaridad',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Descripción', lambda o: o.descripcion),
            ('Estatus', lambda o: o.estatus),
        ],
        'order_by': ['clave'],
    },
    'discapacidad': {
        'model': Discapacidad, 'titulo': 'Discapacidades',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Tipo', lambda o: o.tipo),
            ('Descripción', lambda o: o.descripcion),
        ],
        'order_by': ['clave'],
    },
    'enfermedad': {
        'model': EnfermedadCronica, 'titulo': 'Enfermedades Crónicas',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'pueblo': {
        'model': Pueblo, 'titulo': 'Pueblos Indígenas',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'motivo_baja': {
        'model': MotivoBaja, 'titulo': 'Motivos de Baja',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'idioma': {
        'model': Idioma, 'titulo': 'Idiomas y Lenguas',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('ID CNDH', lambda o: o.identificador_cndh),
            ('Descripción', lambda o: o.descripcion),
            ('Familia Lingüística', lambda o: o.familia_linguistica),
        ],
        'order_by': ['clave'],
    },
    'estado_civil': {
        'model': EstadoCivil, 'titulo': 'Estados Civiles',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'pais': {
        'model': Pais, 'titulo': 'Países',
        'columnas': [('Clave', lambda o: o.clave), ('Nombre', lambda o: o.nombre)],
        'order_by': ['nombre'],
    },
    'entidad': {
        'model': EntidadFederativa, 'titulo': 'Entidades Federativas',
        'columnas': [
            ('Clave', lambda o: o.clave),
            ('Abreviatura', lambda o: o.abreviatura),
            ('Nombre', lambda o: o.nombre),
        ],
        'order_by': ['nombre'],
    },
    'municipio': {
        'model': Municipio, 'titulo': 'Municipios',
        'select_related': ['entidad'],
        'columnas': [
            ('Entidad', lambda o: o.entidad.nombre),
            ('Abreviatura', lambda o: o.abreviatura),
            ('Clave', lambda o: o.clave),
            ('Nombre', lambda o: o.nombre),
        ],
        'order_by': ['entidad__nombre', 'nombre'],
    },
    'sindicato': {
        'model': Sindicato, 'titulo': 'Sindicatos',
        'columnas': [('Clave', lambda o: o.clave), ('Descripción', lambda o: o.descripcion)],
        'order_by': ['clave'],
    },
    'inmueble': {
        'model': Inmueble, 'titulo': 'Inmuebles',
        'select_related': ['dependencia'],
        'columnas': [
            ('Dependencia', lambda o: o.dependencia.clave),
            ('Clave', lambda o: o.clave),
            ('Descripción', lambda o: o.descripcion),
            ('Calle', lambda o: o.calle),
            ('Estado', lambda o: o.estado),
            ('Municipio', lambda o: o.municipio),
            ('Localidad', lambda o: o.localidad),
            ('Núm. Ext.', lambda o: o.num_exterior),
            ('Núm. Int.', lambda o: o.num_interior),
            ('Colonia', lambda o: o.colonia),
            ('CP', lambda o: o.cp),
            ('Teléfono', lambda o: o.telefono),
            ('Tipo Contrato', lambda o: o.get_tipo_contrato_display() if o.tipo_contrato else ''),
            ('Superficie Total', lambda o: float(o.superficie_total) if o.superficie_total is not None else ''),
            ('Superficie Construida', lambda o: float(o.superficie_construida) if o.superficie_construida is not None else ''),
        ],
        'dependencia_lookup': 'dependencia', 'order_by': ['dependencia__clave', 'clave'],
    },
}
