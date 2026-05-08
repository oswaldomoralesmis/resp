from django.urls import path
from . import views

urlpatterns = [
    path('', views.UsuarioListView.as_view(), name='usuario_list'),
    path('nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('<int:pk>/inactivar/', views.inactivar_usuario, name='usuario_inactivar'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('perfil/', views.perfil, name='perfil'),
]
