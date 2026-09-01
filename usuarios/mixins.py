# -*- coding: utf-8 -*-
"""Control de acceso por dependencia: todo usuario que no sea administrador
solo debe ver/editar información de la dependencia que tiene asignada."""
from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdministradorRequiredMixin(UserPassesTestMixin):
    """Restringe la vista a usuarios con rol='administrador'."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_administrador


def admin_requerido(view_func):
    """Para vistas basadas en función: exige rol='administrador'. A diferencia
    de user_passes_test, responde 403 (no redirige al login) cuando el usuario
    ya está autenticado pero no tiene permiso, igual que AdministradorRequiredMixin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.es_administrador):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def usuario_tiene_permiso(user, clave_opcion):
    """Si 'user' puede entrar a la opción de menú 'clave_opcion' (ver
    OpcionAplicativo/RolPermiso). El administrador siempre tiene acceso
    total, sin excepción — no depende de que exista/esté marcada la fila
    de RolPermiso, así nunca se puede dejar sin acceso por un error de
    configuración. Para cualquier otro rol, sin fila RolPermiso = sin
    acceso (deniega por defecto)."""
    if not user.is_authenticated:
        return False
    if user.es_administrador:
        return True
    from .models import RolPermiso
    return RolPermiso.objects.filter(rol=user.rol, opcion__clave=clave_opcion, permitido=True).exists()


class PermisoRequeridoMixin(UserPassesTestMixin):
    """Para vistas basadas en clase: exige que el rol del usuario tenga
    habilitada la opción de menú 'permiso_clave' (ver usuario_tiene_permiso)."""
    permiso_clave = None

    def test_func(self):
        return usuario_tiene_permiso(self.request.user, self.permiso_clave)


def permiso_requerido(clave):
    """Para vistas basadas en función: exige la opción de menú 'clave'."""
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_tiene_permiso(request.user, clave):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador


def puede_revisar_carga(user, carga):
    """Puede aceptar/rechazar una CargaLayout: el administrador (cualquiera),
    o un usuario con rol='validador' de la misma dependencia de la carga."""
    if not user.is_authenticated:
        return False
    if user.es_administrador:
        return True
    return user.rol == 'validador' and user.dependencia_id == carga.dependencia_id


def filtrar_por_dependencia(qs, user, lookup='dependencia'):
    """Limita qs a la dependencia del usuario, salvo que sea administrador
    (que ve todo). 'lookup' es la ruta del filtro, p.ej. 'dependencia',
    'proyecto__dependencia' o 'informacion_basica__dependencia'."""
    if user.is_authenticated and user.es_administrador:
        return qs
    return qs.filter(**{lookup: getattr(user, 'dependencia_id', None)})


class DependenciaScopedMixin:
    """Para ListView/DetailView/UpdateView: si el usuario no es administrador,
    limita el queryset a su propia dependencia. Sirve también como control de
    acceso a objetos individuales, porque get_object() de las vistas genéricas
    de Django resuelve sobre get_queryset() y devuelve 404 si no aparece ahí."""
    dependencia_lookup = 'dependencia'

    def get_queryset(self):
        qs = super().get_queryset()
        return filtrar_por_dependencia(qs, self.request.user, self.dependencia_lookup)


class DependenciaFormRestrictMixin:
    """Para CreateView/UpdateView cuyo form tiene un campo 'dependencia': si
    el usuario no es administrador, limita las opciones del select a su
    propia dependencia y rechaza el POST si de todos modos llega otra
    (por ejemplo, manipulando el HTML)."""
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if 'dependencia' in form.fields and not user.es_administrador:
            form.fields['dependencia'].queryset = form.fields['dependencia'].queryset.filter(pk=user.dependencia_id)
            form.fields['dependencia'].initial = user.dependencia_id
        return form

    def form_valid(self, form):
        user = self.request.user
        if 'dependencia' in form.fields and not user.es_administrador:
            dep = form.cleaned_data.get('dependencia')
            if dep and dep.pk != user.dependencia_id:
                form.add_error('dependencia', 'No tiene permiso para asignar esta dependencia.')
                return self.form_invalid(form)
        return super().form_valid(form)
