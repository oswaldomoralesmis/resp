# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class UsuarioRESP(AbstractUser):
    ROL_CHOICES = [
        ('plantilla', 'Operador'),
        ('validador', 'Validador'),
        ('empleado', 'Empleado'),
        ('consulta', 'Consulta'),
        ('oic', 'OIC'),
        ('general', 'General'),
        ('administrador', 'Administrador'),
    ]
    email = models.EmailField(unique=True, verbose_name='Correo institucional')
    rfc = models.CharField(max_length=13, blank=True, verbose_name='RFC')
    curp = models.CharField(max_length=18, blank=True, verbose_name='CURP')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='empleado', verbose_name='Rol')
    dependencia = models.ForeignKey(
        'catalogos.Dependencia', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Dependencia'
    )
    activo_sistema = models.BooleanField(default=True, verbose_name='Activo en sistema')
    motivo_baja = models.TextField(blank=True, verbose_name='Motivo de baja')
    contrasena_temporal = models.BooleanField(default=True, verbose_name='Contraseña temporal')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'rfc', 'curp']

    class Meta:
        verbose_name = 'Usuario RESP'
        verbose_name_plural = 'Usuarios RESP'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def es_administrador(self):
        return self.rol == 'administrador'

    def clean(self):
        super().clean()
        # Solo se exige para cuentas activas: un usuario recién auto-
        # registrado queda inactivo sin rol/dependencia todavía —
        # corresponde al administrador asignárselos al activarlo.
        if self.is_active and not self.es_administrador and not self.dependencia_id:
            raise ValidationError({
                'dependencia': 'La dependencia es obligatoria para usuarios que no son administradores.'
            })


# Roles configurables desde el módulo de permisos — Administrador queda
# fuera a propósito: siempre tiene acceso total a todo el sistema, no se
# puede quitar desde esta pantalla (evita dejar el sistema sin ningún
# usuario que pueda entrar a corregirlo si alguien se equivoca marcando
# casillas).
ROLES_CONFIGURABLES = [c for c in UsuarioRESP.ROL_CHOICES if c[0] != 'administrador']


class OpcionAplicativo(models.Model):
    """Catálogo de las opciones del menú principal que se pueden habilitar
    o no por rol (ver RolPermiso). Una fila por cada destino de navegación
    de primer nivel — 'Catálogos' es una sola opción para los ~25
    sub-catálogos que agrupa, no una por cada uno."""
    clave = models.CharField(max_length=50, unique=True, verbose_name='Clave')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    modulo = models.CharField(max_length=50, verbose_name='Módulo')
    orden = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Opción del Aplicativo'
        verbose_name_plural = 'Opciones del Aplicativo'
        ordering = ['orden', 'modulo', 'nombre']

    def __str__(self):
        return f"{self.modulo} — {self.nombre}"


class RolPermiso(models.Model):
    """Si un rol (no-administrador) puede entrar a una OpcionAplicativo.
    Sin fila = sin permiso (deniega por defecto)."""
    rol = models.CharField(max_length=20, choices=ROLES_CONFIGURABLES, verbose_name='Rol')
    opcion = models.ForeignKey(
        OpcionAplicativo, on_delete=models.CASCADE, related_name='permisos', verbose_name='Opción',
    )
    permitido = models.BooleanField(default=False, verbose_name='Permitido')

    class Meta:
        verbose_name = 'Permiso de Rol'
        verbose_name_plural = 'Permisos de Roles'
        unique_together = ['rol', 'opcion']

    def __str__(self):
        return f"{self.get_rol_display()} — {self.opcion.nombre}: {'Sí' if self.permitido else 'No'}"
