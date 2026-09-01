# -*- coding: utf-8 -*-
import secrets
import string
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .models import UsuarioRESP, OpcionAplicativo, RolPermiso, ROLES_CONFIGURABLES
from .forms import UsuarioRESPForm, UsuarioRESPEditForm, RegistroForm, ActivarUsuarioForm
from .mixins import AdministradorRequiredMixin, admin_requerido, PermisoRequeridoMixin, permiso_requerido


def registro(request):
    """Auto-registro público (sin login). La cuenta queda inactiva —
    is_active=False— hasta que un administrador la active asignándole rol
    y dependencia (ver activar_usuario)."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request,
                f'Su registro fue recibido, {usuario.first_name}. Un administrador debe activar su '
                'cuenta (asignarle rol y dependencia) antes de que pueda iniciar sesión.'
            )
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form, 'titulo': 'Crear cuenta'})


class UsuarioListView(LoginRequiredMixin, PermisoRequeridoMixin, ListView):
    permiso_clave = 'usuarios'
    model = UsuarioRESP
    template_name = 'usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_queryset(self):
        qs = UsuarioRESP.objects.all().order_by('-fecha_registro')
        estado = self.request.GET.get('estado', '')
        if estado == 'pendientes':
            qs = qs.filter(is_active=False, motivo_baja='')
        elif estado == 'activos':
            qs = qs.filter(activo_sistema=True)
        elif estado == 'inactivos':
            qs = qs.filter(activo_sistema=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Control de Usuarios'
        ctx['estado'] = self.request.GET.get('estado', '')
        ctx['pendientes_count'] = UsuarioRESP.objects.filter(is_active=False, motivo_baja='').count()
        return ctx


class UsuarioCreateView(LoginRequiredMixin, PermisoRequeridoMixin, CreateView):
    permiso_clave = 'usuarios'
    model = UsuarioRESP
    form_class = UsuarioRESPForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Registrar Usuario'
        return ctx


class UsuarioUpdateView(LoginRequiredMixin, PermisoRequeridoMixin, UpdateView):
    permiso_clave = 'usuarios'
    model = UsuarioRESP
    form_class = UsuarioRESPEditForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Usuario'
        return ctx


@login_required
@permiso_requerido('usuarios')
def inactivar_usuario(request, pk):
    usuario = get_object_or_404(UsuarioRESP, pk=pk)
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        usuario.activo_sistema = False
        usuario.is_active = False
        usuario.motivo_baja = motivo
        usuario.save()
        messages.success(request, f'Usuario {usuario.email} inactivado.')
        return redirect('usuario_list')
    return render(request, 'usuarios/inactivar.html', {'usuario': usuario})


@login_required
@permiso_requerido('usuarios')
def activar_usuario(request, pk):
    """Activa a un usuario (auto-registrado y pendiente, o reactivando a
    uno dado de baja antes), asignándole/confirmándole rol y dependencia."""
    usuario = get_object_or_404(UsuarioRESP, pk=pk)
    if request.method == 'POST':
        form = ActivarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = True
            usuario.activo_sistema = True
            usuario.motivo_baja = ''
            usuario.save()
            messages.success(request, f'Usuario {usuario.email} activado. Ya puede iniciar sesión.')
            return redirect('usuario_list')
    else:
        form = ActivarUsuarioForm(instance=usuario)
    return render(request, 'usuarios/activar.html', {'usuario': usuario, 'form': form, 'titulo': 'Activar Usuario'})


@login_required
@permiso_requerido('usuarios')
def resetear_contrasena(request, pk):
    """Genera una contraseña temporal aleatoria para el usuario y la marca
    como 'contraseña temporal' para que la cambie en su próximo ingreso."""
    usuario = get_object_or_404(UsuarioRESP, pk=pk)
    if request.method == 'POST':
        alfabeto = string.ascii_letters + string.digits
        nueva_contrasena = ''.join(secrets.choice(alfabeto) for _ in range(12))
        usuario.set_password(nueva_contrasena)
        usuario.contrasena_temporal = True
        usuario.save()
        return render(request, 'usuarios/reset_contrasena_ok.html', {
            'usuario': usuario, 'nueva_contrasena': nueva_contrasena, 'titulo': 'Contraseña Restablecida',
        })
    return render(request, 'usuarios/reset_contrasena_confirm.html', {
        'usuario': usuario, 'titulo': 'Restablecer Contraseña',
    })


@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.contrasena_temporal = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'usuarios/cambiar_contrasena.html', {'form': form, 'titulo': 'Cambiar Contraseña'})


@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html', {'titulo': 'Mi Perfil'})


@login_required
@admin_requerido
def permisos_rol(request):
    """Matriz Rol × Opción del menú: qué puede ver/entrar cada rol.
    A propósito NO usa permiso_requerido('usuarios') ni ninguna otra clave
    configurable — queda fija en admin_requerido para que nunca se pueda
    dar a un rol la posibilidad de otorgarse permisos a sí mismo."""
    opciones = OpcionAplicativo.objects.all().order_by('orden', 'modulo', 'nombre')

    if request.method == 'POST':
        for opcion in opciones:
            for rol_key, _rol_label in ROLES_CONFIGURABLES:
                permitido = request.POST.get(f'perm_{opcion.pk}_{rol_key}') == 'on'
                RolPermiso.objects.update_or_create(
                    rol=rol_key, opcion=opcion, defaults={'permitido': permitido},
                )
        messages.success(request, 'Permisos actualizados.')
        return redirect('permisos_rol')

    permisos_actuales = {
        (p.opcion_id, p.rol): p.permitido
        for p in RolPermiso.objects.all()
    }
    modulos = {}
    for opcion in opciones:
        modulos.setdefault(opcion.modulo, []).append({
            'opcion': opcion,
            'permisos': [
                {
                    'campo': f'perm_{opcion.pk}_{rol_key}',
                    'permitido': permisos_actuales.get((opcion.pk, rol_key), False),
                }
                for rol_key, _rol_label in ROLES_CONFIGURABLES
            ],
        })

    return render(request, 'usuarios/permisos_rol.html', {
        'modulos': modulos,
        'roles': ROLES_CONFIGURABLES,
        'titulo': 'Permisos por Rol',
    })
