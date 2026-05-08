from django.urls import path
from . import views

urlpatterns = [
    path('', views.CargaListView.as_view(), name='carga_list'),
    path('nueva/', views.carga_layout, name='carga_new'),
    path('<int:pk>/', views.carga_detalle, name='carga_detalle'),
    path('calendario/', views.calendario_cargas, name='calendario_cargas'),
    path('periodos/', views.PeriodoCargaListView.as_view(), name='periodo_list'),
    path('periodos/nuevo/', views.PeriodoCargaCreateView.as_view(), name='periodo_create'),
    path('descargar-plantilla/<str:tipo>/', views.descargar_plantilla, name='descargar_plantilla'),
]
