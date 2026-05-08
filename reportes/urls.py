from django.urls import path
from . import views

urlpatterns = [
    path('', views.reporte_index, name='reporte_index'),
    path('padron/', views.reporte_padron, name='reporte_padron'),
    path('bajas/', views.reporte_bajas, name='reporte_bajas'),
    path('declaracion-patrimonial/', views.reporte_declaracion, name='reporte_declaracion'),
    path('entrega-recepcion/', views.reporte_entrega_recepcion, name='reporte_entrega_recepcion'),
    path('compatibilidad-horarios/', views.reporte_compatibilidad, name='reporte_compatibilidad'),
    path('estadisticas/', views.reporte_estadisticas, name='reporte_estadisticas'),
    path('exportar/<str:tipo>/', views.exportar_excel, name='exportar_excel'),
]
