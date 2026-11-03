from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    path('', views.listar_citas, name='listar_citas'),
    path('detalle/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('estado/<str:estado_filtro>/', views.filtrar_citas, name='filtrar_citas'),
    path('agendar/', views.agendar_cita, name='crear_cita'),
    path('reprogramar/<int:cita_id>/', views.reprogramar_cita, name='reprogramar_cita'),
    path('cancelar/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),
    path('editar/<int:cita_id>/', views.actualizar_cita, name='actualizar_cita'),
    path('eliminar/<int:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
    path('horarios/', views.listar_horarios, name='listar_horarios'),
    path('horarios/crear/', views.editar_horario, name='crear_horario'),
    path('horarios/<int:horario_id>/editar/', views.editar_horario, name='editar_horario'),
]
