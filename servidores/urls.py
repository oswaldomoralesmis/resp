from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect_to_dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('servidores/', views.ServidorListView.as_view(), name='servidor_list'),
    path('servidores/nuevo/', views.ServidorCreateView.as_view(), name='servidor_create'),
    path('servidores/<int:pk>/', views.ServidorDetailView.as_view(), name='servidor_detail'),
    path('servidores/<int:pk>/editar/', views.ServidorUpdateView.as_view(), name='servidor_update'),
    path('servidores/<int:pk>/baja/', views.servidor_baja, name='servidor_baja'),
    path('servidores/<int:pk>/hoja-resp/', views.hoja_resp, name='hoja_resp'),
    path('informacion-basica/', views.InformacionBasicaListView.as_view(), name='info_basica_list'),
    path('informacion-basica/nueva/', views.InformacionBasicaCreateView.as_view(), name='info_basica_create'),
    path('informacion-basica/<int:pk>/editar/', views.InformacionBasicaUpdateView.as_view(), name='info_basica_update'),
]

