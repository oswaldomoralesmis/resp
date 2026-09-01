# -*- coding: utf-8 -*-
"""Pone 'opciones_permitidas' (qué puede VER el usuario en sesión) y
'opciones_editables' (en cuáles de esas además puede crear/editar, para
las opciones con tiene_edicion=True) disponibles en todos los templates,
para que los botones de Nuevo/Editar se oculten solos sin que cada vista
tenga que calcularlo por su cuenta."""
from .models import OpcionAplicativo, RolPermiso


def permisos(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    if user.es_administrador:
        opciones = set(OpcionAplicativo.objects.values_list('clave', flat=True))
        editables = set(OpcionAplicativo.objects.filter(tiene_edicion=True).values_list('clave', flat=True))
    else:
        permisos_rol = RolPermiso.objects.filter(rol=user.rol, permitido=True)
        opciones = set(permisos_rol.values_list('opcion__clave', flat=True))
        editables = set(permisos_rol.filter(puede_editar=True).values_list('opcion__clave', flat=True))
    return {'opciones_permitidas': opciones, 'opciones_editables': editables}
