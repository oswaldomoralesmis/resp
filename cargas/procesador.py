# -*- coding: utf-8 -*-
"""
Procesador de layouts para el RESP.

Columnas del Layout Básico (orden exacto del archivo oficial):
 0  FUENTE FINANCIAMIENTO
 1  DEPENDENCIA
 2  UNIDAD
 3  PROGRAMA
 4  PROYECTO
 5  CATEGORIA
 6  TIPO CONTRATACION
 7  TIPO PERSONAL
 8  TIPO FUNCION
 9  NIVEL ESTRUCTURA
10  ID PUESTO
11  ID PUESTO JEFE
12  HSM
13  PERCEPCIONES
14  BONOS
15  NETO
16  DIAS PAGADOS
17  ESTATUS PLAZA
18  EXPEDIENTE
19  RFC
20  CURP
21  NOMBRE
22  PRIMER APELLIDO
23  SEGUNDO APELLIDO
24  FECHA NACIMIENTO
25  GENERO
26  ESTADO CIVIL
27  ENTIDAD
28  PAIS
29  CORREO ELECTRONICO
30  ISS
31  NSS
32  CENTRO TRABAJO
33  SINDICALIZADO
34  SINDICATO
35  ORDP               (Obligado Declaracion Patrimonial S/N/NULL)
36  TIPO DECLARACION
37  OPAAER             (Obligado Presentar Acta Entrega-Recepcion S/N/NULL)
38  RENCTA             (Rinde Cuentas S/N/NULL)
39  PRDMIS             (Puesto Responsabilidad Decision / Manejo Info Sensible S/N/NULL)
40  OTRA PLAZA
41  FECHA INGRESO GOBIERNO
42  FECHA INGRESO DEPENDENCIA
43  FECHA INGRESO PUESTO
44  AREA
45  PARCONPUB          (Participa Contrataciones Publicas S/N)
46  CONTRATACION PUBLICA (nivel A/B/C/NULL)
47  PARCON             (Participa Concesiones S/N)
48  CONCESIONES        (nivel A/B/C/NULL)
49  PARENA             (Participa Enajenacion S/N)
50  ENAJENACION        (nivel A/B/C/NULL)
51  INMUEBLE           (clave inmueble)
"""
import logging
from datetime import datetime, date

from openpyxl import load_workbook

from catalogos.models import (
    FuenteFinanciamiento, Dependencia, UnidadAdministrativa,
    Programa, Proyecto, Categoria, TipoContratacion, TipoPersonal,
    TipoFuncion, NivelEstructura, EstatusPlaza, CentroTrabajo,
    TipoDeclaracion, Area, EntidadFederativa, Pais, Inmueble,
    EstadoCivil, Sindicato,
)
from servidores.models import ServidorPublico, InformacionBasica

logger = logging.getLogger(__name__)

# ── Índices de columna (base 0) ───────────────────────────────────────────────
C_FTE_FINAN      = 0
C_DEPENDENCIA    = 1
C_UNIDAD         = 2
C_PROGRAMA       = 3
C_PROYECTO       = 4
C_CATEGORIA      = 5
C_TIPO_CONTRA    = 6
C_TIPO_PERSONAL  = 7
C_TIPO_FUNCION   = 8
C_NIVEL_EST      = 9
C_ID_PUESTO      = 10
C_ID_PUESTO_JEFE = 11
C_HSM            = 12
C_PERCEPCIONES   = 13
C_BONOS          = 14
C_NETO           = 15
C_DIAS_PAGADOS   = 16
C_ESTATUS_PLAZA  = 17
C_EXPEDIENTE     = 18
C_RFC            = 19
C_CURP           = 20
C_NOMBRE         = 21
C_PRIMER_AP      = 22
C_SEGUNDO_AP     = 23
C_FECHA_NAC      = 24
C_GENERO         = 25
C_ESTADO_CIVIL   = 26
C_ENTIDAD        = 27
C_PAIS           = 28
C_CORREO         = 29
C_ISS            = 30
C_NSS            = 31
C_CCT            = 32
C_SINDICALIZADO  = 33
C_SINDICATO      = 34
C_ORDP           = 35   # Obligado Declaracion Patrimonial
C_TIPO_DECLA     = 36
C_OPAAER         = 37   # Obligado Entrega-Recepcion
C_RENCTA         = 38   # Rinde Cuentas
C_PRDMIS         = 39   # Puesto Resp. Decision / Info Sensible
C_OTRA_PLAZA     = 40
C_F_INGOB        = 41   # Fecha Ingreso Gobierno
C_F_INDEP        = 42   # Fecha Ingreso Dependencia
C_F_INPUES       = 43   # Fecha Ingreso Puesto
C_AREA           = 44
C_PARCONPUB      = 45   # Participa Contrataciones
C_CONTRAT_PUB    = 46   # Nivel Contrataciones
C_PARCON         = 47   # Participa Concesiones
C_CONCESIONES    = 48   # Nivel Concesiones
C_PARENA         = 49   # Participa Enajenacion
C_ENAJENACION    = 50   # Nivel Enajenacion
C_INMUEBLE       = 51


# ── Helpers ───────────────────────────────────────────────────────────────────
def sv(v, default=''):
    """Safe string, fuerza mayúsculas, limpia NULL."""
    if v is None:
        return default
    s = str(v).strip().upper()
    return s if s not in ('NULL', 'NONE', 'N/A', '') else default


def sd(v, default=''):
    """Safe string, preserva case."""
    if v is None:
        return default
    s = str(v).strip()
    return s if s.upper() not in ('NULL', 'NONE', 'N/A', '') else default


def sf(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def si(v, default=0):
    try:
        return int(float(str(v))) if v is not None else default
    except (ValueError, TypeError):
        return default


def parse_fecha(v):
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.date() if isinstance(v, datetime) else v
    s = str(v).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def normalizar_sexo(v):
    s = sv(v)
    if s in ('M', 'MASCULINO', 'H', 'HOMBRE', 'MALE', '1'):
        return 'MASCULINO'
    if s in ('F', 'FEMENINO', 'MUJER', 'FEMALE', '2'):
        return 'FEMENINO'
    return 'OTRO'


def normalizar_sino(v):
    s = sv(v)
    if s in ('S', 'SI', 'YES', '1', 'TRUE'):
        return 'S'
    if s in ('N', 'NO', '0', 'FALSE'):
        return 'N'
    return 'NULL'


def normalizar_iss(v):
    s = sv(v)
    if 'ISSET' in s:
        return 'ISSET'
    if 'IMSS' in s:
        return 'IMSS'
    if 'ISSSTE' in s:
        return 'ISSSTE'
    return 'ISSET'


# ── Caché de catálogos ────────────────────────────────────────────────────────
class Cache:
    def __init__(self):
        self._d = {}

    def _get(self, key, fn):
        if key not in self._d:
            self._d[key] = fn()
        return self._d[key]

    def fuente(self, v):
        k = sv(v)
        return self._get(f'fte_{k}', lambda: FuenteFinanciamiento.objects.filter(clave=k).first())

    def dependencia(self, v):
        k = sv(v)
        return self._get(f'dep_{k}', lambda: Dependencia.objects.filter(clave=k).first())

    def unidad(self, v):
        k = sv(v)
        return self._get(f'uni_{k}', lambda: UnidadAdministrativa.objects.filter(clave=k).first())

    def programa(self, v):
        k = sv(v)
        return self._get(f'prg_{k}', lambda: Programa.objects.filter(clave=k).first())

    def proyecto(self, v, dependencia=None):
        k = sd(v).strip()
        key = f'pry_{k}_{dependencia.pk if dependencia else ""}'

        def _buscar():
            # Buscar proyecto exacto
            pry = Proyecto.objects.filter(clave__iexact=k).first()
            if pry:
                return pry
            # Si la clave es 00000000 o no se encontró, usar el proyecto default
            if k in ('00000000', '', '0'):
                # Proyecto default vinculado a la dependencia
                if dependencia:
                    pry_def = Proyecto.objects.filter(
                        clave='00000000',
                        dependencia=dependencia
                    ).first()
                    if pry_def:
                        return pry_def
                # Cualquier proyecto default
                return Proyecto.objects.filter(clave='00000000').first()
            return None

        return self._get(key, _buscar)

    def categoria(self, v):
        k = sv(v)
        return self._get(f'cat_{k}', lambda: Categoria.objects.filter(clave=k).first())

    def tipo_contratacion(self, v):
        k = sv(v)
        return self._get(f'tc_{k}', lambda: (
            TipoContratacion.objects.filter(clave=k).first() or
            TipoContratacion.objects.filter(descripcion__icontains=k).first()
        ))

    def tipo_personal(self, v):
        k = sv(v)
        return self._get(f'tp_{k}', lambda: TipoPersonal.objects.filter(clave=k).first())

    def tipo_funcion(self, v):
        k = sv(v)
        return self._get(f'tf_{k}', lambda: TipoFuncion.objects.filter(clave=k).first())

    def nivel_estructura(self, v):
        k = si(v)
        return self._get(f'ne_{k}', lambda: NivelEstructura.objects.filter(nivel=k).first())

    def estatus_plaza(self, v):
        k = sv(v)
        return self._get(f'ep_{k}', lambda: (
            EstatusPlaza.objects.filter(clave=k).first() or
            EstatusPlaza.objects.filter(descripcion__icontains=k).first()
        ))

    def centro_trabajo(self, v):
        k = sd(v)
        return self._get(f'cct_{k}', lambda: CentroTrabajo.objects.filter(clave__iexact=k).first())

    def tipo_declaracion(self, v):
        k = sv(v)
        return self._get(f'td_{k}', lambda: (
            TipoDeclaracion.objects.filter(clave=k).first() or
            TipoDeclaracion.objects.filter(descripcion__icontains=k).first()
        ))

    def area(self, v):
        k = sv(v)
        return self._get(f'ar_{k}', lambda: Area.objects.filter(clave=k).first())

    def entidad(self, v):
        k = sv(v)
        return self._get(f'ent_{k}', lambda: (
            EntidadFederativa.objects.filter(clave=si(v)).first() if str(v).strip().isdigit()
            else EntidadFederativa.objects.filter(nombre__icontains=k).first()
        ))

    def pais(self, v):
        k = sv(v)
        return self._get(f'pai_{k}', lambda: (
            Pais.objects.filter(clave=si(v)).first() if str(v).strip().isdigit()
            else Pais.objects.filter(nombre__icontains=k).first()
            or Pais.objects.filter(clave=700).first()
        ))

    def estado_civil(self, v):
        k = sv(v)
        return self._get(f'ec_{k}', lambda: EstadoCivil.objects.filter(clave=k).first())

    def sindicato(self, v):
        k = sv(v)
        return self._get(f'sin_{k}', lambda: Sindicato.objects.filter(clave=k).first())

    def inmueble(self, v):
        k = sd(v)
        if not k:
            return None
        return self._get(f'inm_{k}', lambda: Inmueble.objects.filter(clave__iexact=k).first())


# ── Procesador principal ──────────────────────────────────────────────────────
def procesar_layout_basica(carga):
    ruta     = carga.archivo.path
    quincena = carga.periodo.quincena
    log      = []
    ok       = 0
    errores  = 0
    total    = 0

    try:
        wb = load_workbook(ruta, read_only=True, data_only=True)
    except Exception as e:
        return {'ok': 0, 'errores': 1, 'total': 0, 'log': f'No se pudo abrir el archivo: {e}'}

    # Buscar la hoja correcta: primero "LAYOUT", luego la activa
    hoja = wb['LAYOUT'] if 'LAYOUT' in wb.sheetnames else wb.active
    filas = list(hoja.iter_rows(values_only=True))

    # Detectar la fila de encabezados buscando "RFC" o "CURP"
    inicio_datos = 1   # default: datos desde fila 2 (índice 1)
    for idx, fila in enumerate(filas):
        fila_str = [str(c).upper().strip() if c else '' for c in fila]
        if 'RFC' in fila_str or 'CURP' in fila_str:
            inicio_datos = idx + 1
            break

    cache = Cache()

    for num_fila, fila in enumerate(filas[inicio_datos:], start=inicio_datos + 1):
        if not any(c is not None for c in fila):
            continue

        total += 1
        errores_fila = []

        def col(i, default=None):
            try:
                v = fila[i]
                if v is None or str(v).strip().upper() in ('NULL', 'NONE', 'N/A', ''):
                    return default
                return v
            except IndexError:
                return default

        # ── Campos obligatorios ──────────────────────────────────────────────
        rfc    = sv(col(C_RFC))
        curp   = sv(col(C_CURP))
        nombre = sd(col(C_NOMBRE, '')).upper()
        ap_pat = sd(col(C_PRIMER_AP, '')).upper()

        if not rfc:
            errores_fila.append('RFC vacío')
        if not curp:
            errores_fila.append('CURP vacío')
        if not nombre:
            errores_fila.append('Nombre vacío')
        if not ap_pat:
            errores_fila.append('Primer apellido vacío')

        if errores_fila:
            errores += 1
            log.append(f'Fila {num_fila}: OMITIDA — {", ".join(errores_fila)}')
            continue

        ap_mat     = sd(col(C_SEGUNDO_AP, '')).upper() or None
        expediente = sd(col(C_EXPEDIENTE, '')) or f'EXP-{rfc}'

        # ── Servidor Público: buscar o crear ─────────────────────────────────
        try:
            servidor, creado = ServidorPublico.objects.get_or_create(
                rfc=rfc,
                defaults={
                    'curp':                  curp,
                    'expediente':            expediente,
                    'nombre':                nombre,
                    'primer_apellido':       ap_pat,
                    'segundo_apellido':      ap_mat,
                    'fecha_nacimiento':      parse_fecha(col(C_FECHA_NAC)) or date(1900, 1, 1),
                    'sexo':                  normalizar_sexo(col(C_GENERO)),
                    'estado_civil':          cache.estado_civil(col(C_ESTADO_CIVIL)),
                    'entidad_nacimiento':    cache.entidad(col(C_ENTIDAD)),
                    'pais_nacimiento':       cache.pais(col(C_PAIS)),
                    'correo_institucional':  sd(col(C_CORREO, '')),
                    'iss':                   normalizar_iss(col(C_ISS)),
                    'nss':                   sd(col(C_NSS, '')),
                    'sindicalizado':         normalizar_sino(col(C_SINDICALIZADO)),
                    'sindicato':             cache.sindicato(col(C_SINDICATO)),
                    'tiene_otra_plaza':      normalizar_sino(col(C_OTRA_PLAZA)),
                    'activo':                True,
                }
            )
            if not creado:
                # Actualizar campos que pueden cambiar quincenalmente
                cambios = False
                nuevo_correo = sd(col(C_CORREO, ''))
                nuevo_nss    = sd(col(C_NSS, ''))
                if nuevo_correo and servidor.correo_institucional != nuevo_correo:
                    servidor.correo_institucional = nuevo_correo; cambios = True
                if nuevo_nss and servidor.nss != nuevo_nss:
                    servidor.nss = nuevo_nss; cambios = True
                if ap_mat and servidor.segundo_apellido != ap_mat:
                    servidor.segundo_apellido = ap_mat; cambios = True
                ec = cache.estado_civil(col(C_ESTADO_CIVIL))
                if ec and servidor.estado_civil != ec:
                    servidor.estado_civil = ec; cambios = True
                sin = cache.sindicato(col(C_SINDICATO))
                if sin and servidor.sindicato != sin:
                    servidor.sindicato = sin; cambios = True
                if cambios:
                    servidor.save()

        except Exception as e:
            # Posible CURP duplicado con otro RFC
            try:
                servidor = ServidorPublico.objects.get(curp=curp)
            except ServidorPublico.DoesNotExist:
                errores += 1
                log.append(f'Fila {num_fila} RFC={rfc}: ERROR creando servidor — {e}')
                continue

        # ── Catálogos del puesto ─────────────────────────────────────────────
        fuente      = cache.fuente(col(C_FTE_FINAN))
        dependencia = cache.dependencia(col(C_DEPENDENCIA))
        unidad      = cache.unidad(col(C_UNIDAD))
        programa    = cache.programa(col(C_PROGRAMA))
        proyecto    = cache.proyecto(col(C_PROYECTO), dependencia=dependencia)
        categoria   = cache.categoria(col(C_CATEGORIA))
        nombramiento= cache.tipo_contratacion(col(C_TIPO_CONTRA))
        tipo_pers   = cache.tipo_personal(col(C_TIPO_PERSONAL))
        tipo_fun    = cache.tipo_funcion(col(C_TIPO_FUNCION))
        nivel_est   = cache.nivel_estructura(col(C_NIVEL_EST))
        estatus     = cache.estatus_plaza(col(C_ESTATUS_PLAZA))
        cct         = cache.centro_trabajo(col(C_CCT))
        tipo_decla  = cache.tipo_declaracion(col(C_TIPO_DECLA))
        area        = cache.area(col(C_AREA))
        inmueble    = cache.inmueble(col(C_INMUEBLE))

        avisos = []
        if not dependencia:
            avisos.append(f'Dependencia "{col(C_DEPENDENCIA)}" no encontrada')
        if not estatus:
            avisos.append(f'Estatus plaza "{col(C_ESTATUS_PLAZA)}" no encontrado')
        if not nombramiento:
            avisos.append(f'Tipo contratación "{col(C_TIPO_CONTRA)}" no encontrado')

        # ── Desactivar registro anterior de la misma plaza+quincena ──────────
        InformacionBasica.objects.filter(
            servidor=servidor,
            quincena=quincena,
            id_plaza=sd(col(C_ID_PUESTO, '')),
        ).update(activo=False)

        # ── Crear registro de Información Básica ─────────────────────────────
        try:
            InformacionBasica.objects.create(
                # Institución
                fuente_financiamiento      = fuente,
                dependencia                = dependencia,
                unidad                     = unidad,
                programa                   = programa,
                proyecto                   = proyecto,
                # Puesto
                id_plaza                   = sd(col(C_ID_PUESTO, '')),
                categoria                  = categoria,
                puesto                     = sd(col(C_ID_PUESTO, '')),
                nombramiento               = nombramiento,
                nivel_estructura           = nivel_est,
                id_plaza_jefe              = sd(col(C_ID_PUESTO_JEFE, '')),
                puesto_jefe                = sd(col(C_ID_PUESTO_JEFE, '')),
                hsm                        = sf(col(C_HSM)),
                total_percepciones         = sf(col(C_PERCEPCIONES)),
                total_bonos                = sf(col(C_BONOS)),
                total_neto                 = sf(col(C_NETO)),
                dias_pagados               = si(col(C_DIAS_PAGADOS)),
                estatus_plaza              = estatus,
                # Servidor
                servidor                   = servidor,
                cct                        = cct,
                # Persona-Puesto
                oblig_declaracion          = normalizar_sino(col(C_ORDP)),
                tipo_declaracion           = tipo_decla,
                oblig_entrega_recepcion    = normalizar_sino(col(C_OPAAER)),
                oblig_rendir_cuentas       = normalizar_sino(col(C_RENCTA)),
                puesto_sensible            = normalizar_sino(col(C_PRDMIS)),
                # Fechas
                fecha_ingreso_gobierno     = parse_fecha(col(C_F_INGOB)),
                fecha_ingreso_dependencia  = parse_fecha(col(C_F_INDEP)),
                fecha_ingreso_puesto       = parse_fecha(col(C_F_INPUES)),
                # Responsabilidades
                area                       = area,
                participa_contrataciones   = normalizar_sino(col(C_PARCONPUB)),
                nivel_contrataciones       = sd(col(C_CONTRAT_PUB, '')),
                participa_concesiones      = normalizar_sino(col(C_PARCON)),
                nivel_concesiones          = sd(col(C_CONCESIONES, '')),
                participa_enajenacion      = normalizar_sino(col(C_PARENA)),
                nivel_enajenacion          = sd(col(C_ENAJENACION, '')),
                participa_avaluos          = 'N',
                nivel_avaluos              = '',
                # Inmueble
                inmueble                   = inmueble,
                serc                       = 'NULL',
                exigibilidad_serc          = 'NULL',
                # Control
                quincena                   = quincena,
                activo                     = True,
            )
            ok += 1
            accion = 'NUEVO' if creado else 'ACTUALIZADO'
            if avisos:
                log.append(f'Fila {num_fila} RFC={rfc}: OK ({accion}) — Avisos: {"; ".join(avisos)}')

        except Exception as e:
            errores += 1
            log.append(f'Fila {num_fila} RFC={rfc}: ERROR al crear registro — {e}')

    return {
        'ok':      ok,
        'errores': errores,
        'total':   total,
        'log':     '\n'.join(log),
    }
