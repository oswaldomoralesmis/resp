# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .models import UsuarioRESP
from .forms import UsuarioRESPForm


class UsuarioListView(LoginRequiredMixin, ListView):
    model = UsuarioRESP
    template_name = 'usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Control de Usuarios'
        return ctx


class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = UsuarioRESP
    form_class = UsuarioRESPForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Registrar Usuario'
        return ctx


class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = UsuarioRESP
    form_class = UsuarioRESPForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuario_list')


@login_required
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
