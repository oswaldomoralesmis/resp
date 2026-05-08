# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.db import models


class UsuarioRESP(AbstractUser):
    ROL_CHOICES = [
        ('plantilla', 'De Plantilla'),
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
