# -*- coding: utf-8 -*-
from django.db import models


class FuenteFinanciamiento(models.Model):
    clave = models.CharField(max_length=10, unique=True, verbose_name='Clave')
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Fuente de Financiamiento'
        verbose_name_plural = 'Fuentes de Financiamiento'
        ordering = ['clave']

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class Dependencia(models.Model):
    ejercicio = models.IntegerField(default=2025, verbose_name='Ejercicio')
    clave = models.CharField(max_length=5, verbose_name='Clave')
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Dependencia'
        verbose_name_plural = 'Dependencias'
        ordering = ['clave']
        unique_together = ['ejercicio', 'clave']

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class UnidadAdministrativa(models.Model):
    ejercicio = models.IntegerField(default=2025)
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE, verbose_name='Dependencia')
    clave = models.CharField(max_length=10, verbose_name='Clave')
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Unidad Administrativa'
        verbose_name_plural = 'Unidades Administrativas'
        ordering = ['clave']

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class Programa(models.Model):
    ejercicio = models.IntegerField(default=2025)
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE)
    unidad = models.ForeignKey(UnidadAdministrativa, on_delete=models.CASCADE)
    clave = models.CharField(max_length=10, verbose_name='Clave')
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Programa'
        verbose_name_plural = 'Programas'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class Proyecto(models.Model):
    ejercicio = models.IntegerField(default=2025)
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE)
    unidad = models.ForeignKey(UnidadAdministrativa, on_delete=models.CASCADE)
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE)
    clave = models.CharField(max_length=20, verbose_name='Clave')
    descripcion = models.CharField(max_length=300, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class Categoria(models.Model):
    clave = models.CharField(max_length=15, unique=True, verbose_name='Clave')
    subcategoria = models.IntegerField(default=0)
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')
    tipo_plaza = models.CharField(max_length=50, blank=True)
    tp = models.CharField(max_length=5, blank=True)
    nivel = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class TipoContratacion(models.Model):
    clave = models.CharField(max_length=5, unique=True, verbose_name='Clave')
    descripcion = models.CharField(max_length=100, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Tipo de Contratación'
        verbose_name_plural = 'Tipos de Contratación'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class TipoPersonal(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    tipo_contratacion = models.ForeignKey(TipoContratacion, on_delete=models.CASCADE, null=True, blank=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Tipo de Personal'
        verbose_name_plural = 'Tipos de Personal'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class TipoFuncion(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Tipo de Función'
        verbose_name_plural = 'Tipos de Función'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class NivelEstructura(models.Model):
    clave = models.CharField(max_length=15, unique=True)
    descripcion = models.CharField(max_length=100)
    nivel = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Nivel de Estructura'
        verbose_name_plural = 'Niveles de Estructura'
        ordering = ['nivel']

    def __str__(self):
        return f"{self.clave} - {self.descripcion} (Nivel {self.nivel})"


class EstatusPlaza(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Estatus de Plaza'
        verbose_name_plural = 'Estatus de Plaza'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class CentroTrabajo(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    nivel_educativo = models.CharField(max_length=50, blank=True)
    municipio = models.CharField(max_length=100, blank=True)
    domicilio = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = 'Centro de Trabajo'
        verbose_name_plural = 'Centros de Trabajo'

    def __str__(self):
        return f"{self.clave} - {self.nombre}"


class TipoDeclaracion(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Tipo de Declaración'
        verbose_name_plural = 'Tipos de Declaración'

    def __str__(self):
        return self.descripcion


class Area(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class NivelEscolaridad(models.Model):
    clave = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=100)
    estatus = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Nivel de Escolaridad'
        verbose_name_plural = 'Niveles de Escolaridad'

    def __str__(self):
        return f"{self.descripcion} - {self.estatus}"


class Discapacidad(models.Model):
    clave = models.IntegerField(unique=True)
    tipo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Discapacidad'
        verbose_name_plural = 'Discapacidades'

    def __str__(self):
        return self.tipo


class EnfermedadCronica(models.Model):
    clave = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Enfermedad Crónica'
        verbose_name_plural = 'Enfermedades Crónicas'

    def __str__(self):
        return self.descripcion


class Pueblo(models.Model):
    clave = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Pueblo Indígena/Afromexicano'
        verbose_name_plural = 'Pueblos Indígenas/Afromexicanos'

    def __str__(self):
        return self.descripcion


class MotivoBaja(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Motivo de Baja'
        verbose_name_plural = 'Motivos de Baja'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"


class Idioma(models.Model):
    clave = models.IntegerField(unique=True)
    identificador_cndh = models.IntegerField(null=True, blank=True)
    descripcion = models.CharField(max_length=100)
    familia_linguistica = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Idioma/Lengua'
        verbose_name_plural = 'Idiomas/Lenguas'

    def __str__(self):
        return self.descripcion


class EstadoCivil(models.Model):
    clave = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Estado Civil'
        verbose_name_plural = 'Estados Civiles'

    def __str__(self):
        return self.descripcion


class Pais(models.Model):
    clave = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class EntidadFederativa(models.Model):
    clave = models.IntegerField(unique=True)
    abreviatura = models.CharField(max_length=5)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Entidad Federativa'
        verbose_name_plural = 'Entidades Federativas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    abreviatura = models.CharField(max_length=10, blank=True)
    entidad = models.ForeignKey(EntidadFederativa, on_delete=models.CASCADE)
    clave = models.CharField(max_length=5)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.entidad.abreviatura})"


class Sindicato(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Sindicato'
        verbose_name_plural = 'Sindicatos'

    def __str__(self):
        return self.clave


class Inmueble(models.Model):
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE)
    clave = models.CharField(max_length=10, unique=True, verbose_name='Clave')
    descripcion = models.CharField(max_length=200, verbose_name='Descripción')
    calle = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=100, blank=True)
    municipio = models.CharField(max_length=100, blank=True)
    localidad = models.CharField(max_length=100, blank=True)
    num_exterior = models.CharField(max_length=10, blank=True)
    num_interior = models.CharField(max_length=10, blank=True)
    colonia = models.CharField(max_length=100, blank=True)
    cp = models.CharField(max_length=10, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    tipo_contrato = models.CharField(max_length=20, blank=True, choices=[('1', 'Propio'), ('2', 'Arrendamiento')])
    superficie_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    superficie_construida = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Inmueble'
        verbose_name_plural = 'Inmuebles'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"
