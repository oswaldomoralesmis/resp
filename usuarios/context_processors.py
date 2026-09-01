# -*- coding: utf-8 -*-
"""Pone 'opciones_permitidas' (set de claves de OpcionAplicativo que el
usuario en sesión puede ver) disponible en todos los templates, para que
base.html pueda mostrar/ocultar cada link del menú sin que cada vista
tenga que calcularlo por su cuenta."""
from .models import OpcionAplicativo, RolPermiso


def permisos(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    if user.es_administrador:
        opciones = set(OpcionAplicativo.objects.values_list('clave', flat=True))
    else:
        opciones = set(
            RolPermiso.objects.filter(rol=user.rol, permitido=True).values_list('opcion__clave', flat=True)
        )
    return {'opciones_permitidas': opciones}
