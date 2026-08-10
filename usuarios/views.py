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
from .models import UsuarioRESP
from .forms import UsuarioRESPForm, UsuarioRESPEditForm
from .mixins import AdministradorRequiredMixin, admin_requerido


class UsuarioListView(AdministradorRequiredMixin, LoginRequiredMixin, ListView):
    model = UsuarioRESP
    template_name = 'usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Control de Usuarios'
        return ctx


class UsuarioCreateView(AdministradorRequiredMixin, LoginRequiredMixin, CreateView):
    model = UsuarioRESP
    form_class = UsuarioRESPForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Registrar Usuario'
        return ctx


class UsuarioUpdateView(AdministradorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = UsuarioRESP
    form_class = UsuarioRESPEditForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Usuario'
        return ctx


@login_required
@admin_requerido
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
@admin_requerido
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
