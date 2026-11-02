from django.urls import path
from . import views

app_name = "registros_medicos"

urlpatterns = [
    # Lista de Registros Médicos (Página Principal)
    path('', views.listar_registros_medicos, name='listar_registros_medicos'),
    path('registros/crear/', views.crear_registro_medico, name='crear_registro_medico'),
    path('registros/detalle/<str:id>/', views.detalle_registro_medico, name='detalle_registro_medico'),
    path('registros/eliminar/<str:id>/', views.eliminar_registro_medico, name='eliminar_registro_medico'),

    # Laboratorios
    path('laboratorios/', views.listar_estudios_laboratorio, name='listar_estudios_laboratorio'),
    path('laboratorios/crear/', views.crear_estudio_laboratorio, name='crear_estudio_laboratorio'),
    path('laboratorios/actualizar/<str:id>/', views.actualizar_laboratorio, name='actualizar_laboratorio'),
    path('laboratorios/detalle/<str:id>/', views.detalle_laboratorio, name='detalle_laboratorio'),
    path('laboratorios/eliminar-cancelados/', views.eliminar_estudios_cancelados, name='eliminar_estudios_cancelados'),
]