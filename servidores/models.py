# -*- coding: utf-8 -*-
from django.db import models
from catalogos.models import (
    FuenteFinanciamiento, Dependencia, UnidadAdministrativa, Programa,
    Proyecto, Categoria, TipoContratacion, TipoPersonal, TipoFuncion,
    NivelEstructura, EstatusPlaza, CentroTrabajo, TipoDeclaracion, Area,
    NivelEscolaridad, Discapacidad, EnfermedadCronica, Pueblo, Idioma,
    EstadoCivil, Pais, EntidadFederativa, Municipio, Sindicato, Inmueble
)


ISS_CHOICES = [('ISSET', 'ISSET'), ('IMSS', 'IMSS'), ('ISSSTE', 'ISSSTE'), ('NINGUNO', 'Ninguno')]
SINO_NULL = [('S', 'Sí'), ('N', 'No'), ('NULL', 'No aplica')]
SEXO_CHOICES = [('MASCULINO', 'Masculino'), ('FEMENINO', 'Femenino'), ('OTRO', 'Otro')]


class ServidorPublico(models.Model):
    """Información principal del servidor público"""
    expediente = models.CharField(max_length=20, unique=True, verbose_name='No. Expediente')
    rfc = models.CharField(max_length=13, unique=True, verbose_name='RFC')
    curp = models.CharField(max_length=18, unique=True, verbose_name='CURP')
    determinante = models.CharField(max_length=20, blank=True, verbose_name='Determinante')
    nombre = models.CharField(max_length=50, verbose_name='Nombre(s)')
    primer_apellido = models.CharField(max_length=50, verbose_name='Primer Apellido')
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True, verbose_name='Segundo Apellido')
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento')
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, verbose_name='Sexo')
    estado_civil = models.ForeignKey(EstadoCivil, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Estado Civil')
    entidad_nacimiento = models.ForeignKey(EntidadFederativa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Entidad de Nacimiento')
    pais_nacimiento = models.ForeignKey(Pais, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='País de Nacimiento')
    correo_institucional = models.EmailField(blank=True, verbose_name='Correo Institucional')
    iss = models.CharField(max_length=10, choices=ISS_CHOICES, default='ISSET', verbose_name='Instituto de Seguridad Social')
    nss = models.CharField(max_length=20, blank=True, verbose_name='Número de Seguridad Social')
    sindicato = models.ForeignKey(Sindicato, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Sindicato')
    sindicalizado = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='¿Sindicalizado?')
    tiene_otra_plaza = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='¿Tiene otra plaza?')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servidor Público'
        verbose_name_plural = 'Servidores Públicos'
        ordering = ['primer_apellido', 'segundo_apellido', 'nombre']

    def __str__(self):
        return f"{self.primer_apellido} {self.segundo_apellido or ''} {self.nombre} - {self.rfc}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.primer_apellido} {self.segundo_apellido or ''}".strip()


class DatosPersonales(models.Model):
    """Datos personales del servidor público (actualización anual)"""
    servidor = models.OneToOneField(ServidorPublico, on_delete=models.CASCADE, related_name='datos_personales')
    calle = models.CharField(max_length=100, blank=True, verbose_name='Calle y Número')
    num_exterior = models.CharField(max_length=10, blank=True, verbose_name='Núm. Exterior')
    num_interior = models.CharField(max_length=10, blank=True, verbose_name='Núm. Interior')
    colonia = models.CharField(max_length=50, blank=True, verbose_name='Colonia')
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Municipio')
    entidad = models.ForeignKey(EntidadFederativa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Entidad Federativa')
    pais = models.ForeignKey(Pais, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='País')
    cp = models.CharField(max_length=10, blank=True, verbose_name='C.P.')
    correo_personal = models.EmailField(blank=True, null=True, verbose_name='Correo Personal')
    tipo_sangre = models.CharField(max_length=4, blank=True, verbose_name='Tipo de Sangre')
    factor_rh = models.CharField(max_length=10, blank=True, choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], verbose_name='Factor RH')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datos Personales'
        verbose_name_plural = 'Datos Personales'


class DatosComplementarios(models.Model):
    """Información curricular (validada por Validador)"""
    servidor = models.OneToOneField(ServidorPublico, on_delete=models.CASCADE, related_name='datos_complementarios')
    nivel_escolaridad = models.ForeignKey(NivelEscolaridad, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nivel de Escolaridad')
    discapacidad = models.ForeignKey(Discapacidad, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Discapacidad')
    pueblo_indigena = models.ForeignKey(Pueblo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Pueblo Indígena/Afromexicano')
    validado = models.BooleanField(default=False, verbose_name='Validado')
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Datos Complementarios'
        verbose_name_plural = 'Datos Complementarios'


class EnfermedadCronicaServidor(models.Model):
    servidor = models.ForeignKey(ServidorPublico, on_delete=models.CASCADE, related_name='enfermedades')
    enfermedad = models.ForeignKey(EnfermedadCronica, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['servidor', 'enfermedad']


class IdiomaServidor(models.Model):
    servidor = models.ForeignKey(ServidorPublico, on_delete=models.CASCADE, related_name='idiomas')
    idioma = models.ForeignKey(Idioma, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ['servidor', 'idioma']


class Puesto(models.Model):
    """Plaza dentro de la estructura Dependencia-Unidad-Programa-Proyecto.
    Un proyecto puede abarcar varios programas (y por lo tanto varias unidades
    administrativas), así que cada puesto guarda su propio 'programa' además
    del 'proyecto' para saber exactamente en cuál unidad/programa está.
    id_plaza es la llave única de la plaza en todo el gobierno, independiente
    del proyecto al que esté asignada hoy. El estatus se calcula solo a partir
    de si tiene un servidor asignado."""
    ESTATUS_VACANTE = 'vacante'
    ESTATUS_OCUPADA = 'ocupada'
    ESTATUS_CHOICES = [
        (ESTATUS_VACANTE, 'Vacante'),
        (ESTATUS_OCUPADA, 'Ocupada'),
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name='puestos', verbose_name='Proyecto')
    programa = models.ForeignKey(Programa, on_delete=models.PROTECT, related_name='puestos', verbose_name='Programa')
    unidad = models.ForeignKey(UnidadAdministrativa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Unidad Administrativa')
    id_plaza = models.CharField(max_length=20, unique=True, verbose_name='ID de Plaza')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name='Categoría')
    nombramiento = models.ForeignKey(TipoContratacion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Tipo de Contratación')
    nivel_estructura = models.ForeignKey(NivelEstructura, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nivel de Estructura')
    estatus_plaza = models.ForeignKey(EstatusPlaza, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Estatus de Plaza')
    cct = models.ForeignKey(CentroTrabajo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Centro de Trabajo')
    hsm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='HSM (Hora-Semana-Mes)')
    total_percepciones = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Percepciones')
    total_bonos = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Bonos')
    total_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Neto')
    dias_pagados = models.IntegerField(default=0, verbose_name='Días Pagados')
    id_plaza_jefe = models.CharField(max_length=20, blank=True, verbose_name='ID Plaza Jefe Inmediato')
    servidor_actual = models.ForeignKey(
        ServidorPublico, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='puestos_ocupados', verbose_name='Trabajador Asignado'
    )
    estatus = models.CharField(
        max_length=10, choices=ESTATUS_CHOICES, default=ESTATUS_VACANTE,
        editable=False, verbose_name='Estatus'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Puesto'
        verbose_name_plural = 'Puestos'
        ordering = ['proyecto', 'id_plaza']

    def save(self, *args, **kwargs):
        self.estatus = self.ESTATUS_OCUPADA if self.servidor_actual_id else self.ESTATUS_VACANTE
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_plaza} - {self.categoria} ({self.get_estatus_display()})"

    @property
    def jefe_actual(self):
        """Servidor que ocupa la plaza registrada en id_plaza_jefe, si existe."""
        if not self.id_plaza_jefe:
            return None
        jefe = Puesto.objects.filter(id_plaza=self.id_plaza_jefe).select_related('servidor_actual').first()
        return jefe.servidor_actual if jefe else None


def sincronizar_puesto(proyecto, programa, id_plaza, categoria, servidor, **datos_plaza):
    """Crea o actualiza el Puesto identificado por id_plaza (llave única) y lo
    marca ocupado por 'servidor'. Se llama desde la carga de layout y desde el
    alta manual de Información Básica, para que la tabla de puestos siempre
    refleje quién ocupa cada plaza y con qué datos (unidad, sueldo, etc.).

    'datos_plaza' acepta los campos propios de la plaza en Puesto: unidad,
    nombramiento, nivel_estructura, estatus_plaza, cct, hsm,
    total_percepciones, total_bonos, total_neto, dias_pagados. Lo que traiga
    el Excel siempre gana sobre ediciones manuales previas."""
    campos = {'proyecto': proyecto, 'programa': programa, 'categoria': categoria, 'servidor_actual': servidor, **datos_plaza}
    puesto, creado = Puesto.objects.get_or_create(id_plaza=id_plaza, defaults=campos)
    if not creado:
        cambios = False
        for campo, valor in campos.items():
            if getattr(puesto, campo) != valor:
                setattr(puesto, campo, valor)
                cambios = True
        if cambios:
            puesto.save()
    return puesto


def reportar_puesto_vacante(id_plaza, proyecto=None, programa=None, categoria=None):
    """Registra que la plaza id_plaza (llave única) no tiene trabajador asignado.
    Si el puesto ya existe, lo libera; si no existe y se cuenta con proyecto,
    programa y categoría (columnas de institución/puesto de la fila), lo da de
    alta ya vacante. Devuelve None solo si no hay datos suficientes para darlo
    de alta."""
    puesto = Puesto.objects.filter(id_plaza=id_plaza).first()
    if puesto:
        if puesto.servidor_actual_id is not None:
            puesto.servidor_actual = None
            puesto.save()
        return puesto
    if proyecto and programa and categoria:
        return Puesto.objects.create(proyecto=proyecto, programa=programa, id_plaza=id_plaza, categoria=categoria)
    return None


def liberar_puestos_de(servidor):
    """Deja vacantes todos los puestos que ocupaba 'servidor' (p.ej. al darlo de baja)."""
    Puesto.objects.filter(servidor_actual=servidor).update(
        servidor_actual=None, estatus=Puesto.ESTATUS_VACANTE
    )


class InformacionBasica(models.Model):
    """Registro quincenal de ocupación/plaza del servidor público"""
    # Datos de institución
    fuente_financiamiento = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, verbose_name='Fuente de Financiamiento')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT, verbose_name='Dependencia')
    unidad = models.ForeignKey(UnidadAdministrativa, on_delete=models.PROTECT, verbose_name='Unidad Administrativa')
    programa = models.ForeignKey(Programa, on_delete=models.PROTECT, verbose_name='Programa')
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, verbose_name='Proyecto')
    # Puesto
    id_plaza = models.CharField(max_length=20, verbose_name='ID Plaza')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name='Categoría')
    puesto = models.CharField(max_length=20, verbose_name='Puesto')
    nombramiento = models.ForeignKey(TipoContratacion, on_delete=models.PROTECT, verbose_name='Tipo de Contratación')
    nivel_estructura = models.ForeignKey(NivelEstructura, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nivel de Estructura')
    id_plaza_jefe = models.CharField(max_length=20, blank=True, verbose_name='ID Plaza Jefe Inmediato')
    puesto_jefe = models.CharField(max_length=20, blank=True, verbose_name='Puesto Jefe Inmediato')
    hsm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='HSM (Hora-Semana-Mes)')
    total_percepciones = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Percepciones')
    total_bonos = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Bonos')
    total_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Neto')
    dias_pagados = models.IntegerField(default=0, verbose_name='Días Pagados')
    estatus_plaza = models.ForeignKey(EstatusPlaza, on_delete=models.PROTECT, verbose_name='Estatus de Plaza')
    # Servidor
    servidor = models.ForeignKey(ServidorPublico, on_delete=models.PROTECT, related_name='informacion_basica', verbose_name='Servidor Público')
    cct = models.ForeignKey(CentroTrabajo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Centro de Trabajo')
    # Persona-Puesto
    oblig_declaracion = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Obligado a Declaración Patrimonial')
    tipo_declaracion = models.ForeignKey(TipoDeclaracion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Tipo de Declaración')
    oblig_entrega_recepcion = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Oblig. Acta Entrega-Recepción')
    oblig_rendir_cuentas = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Obligado a Rendir Cuentas')
    puesto_sensible = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Puesto con Info. Sensible')
    # Fechas
    fecha_ingreso_gobierno = models.DateField(null=True, blank=True, verbose_name='Fecha Ingreso al Gobierno')
    fecha_ingreso_dependencia = models.DateField(null=True, blank=True, verbose_name='Fecha Ingreso a la Dependencia')
    fecha_ingreso_puesto = models.DateField(null=True, blank=True, verbose_name='Fecha Ingreso al Puesto')
    # Responsabilidades
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Área')
    participa_contrataciones = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Participa en Contrataciones')
    nivel_contrataciones = models.CharField(max_length=10, blank=True, verbose_name='Nivel en Contrataciones')
    participa_concesiones = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Participa en Concesiones')
    nivel_concesiones = models.CharField(max_length=10, blank=True, verbose_name='Nivel en Concesiones')
    participa_enajenacion = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Participa en Enajenación')
    nivel_enajenacion = models.CharField(max_length=10, blank=True, verbose_name='Nivel en Enajenación')
    participa_avaluos = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Participa en Avalúos')
    nivel_avaluos = models.CharField(max_length=10, blank=True, verbose_name='Nivel en Avalúos')
    # Inmueble
    inmueble = models.ForeignKey(Inmueble, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Inmueble')
    serc = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='SERC')
    exigibilidad_serc = models.CharField(max_length=5, choices=SINO_NULL, default='N', verbose_name='Exigibilidad SERC')
    # Control
    quincena = models.CharField(max_length=7, verbose_name='Quincena (AAAA-QQ)')
    fecha_carga = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Información Básica'
        verbose_name_plural = 'Información Básica'
        ordering = ['-quincena', 'dependencia', 'servidor']

    def __str__(self):
        return f"{self.servidor} - {self.quincena} - {self.id_plaza}"


class BajaServidorPublico(models.Model):
    """Registro de baja del servidor público"""
    servidor = models.ForeignKey(ServidorPublico, on_delete=models.PROTECT, related_name='bajas')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT)
    fecha_baja = models.DateField(verbose_name='Fecha de Baja')
    motivo_baja = models.ForeignKey('catalogos.MotivoBaja', on_delete=models.PROTECT, verbose_name='Motivo de Baja')
    ejercicio = models.IntegerField(verbose_name='Ejercicio')
    periodo = models.CharField(max_length=7, verbose_name='Período')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey('usuarios.UsuarioRESP', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Baja de Servidor Público'
        verbose_name_plural = 'Bajas de Servidores Públicos'

    def __str__(self):
        return f"Baja: {self.servidor} - {self.fecha_baja}"
