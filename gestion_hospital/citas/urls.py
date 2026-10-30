from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    path('', views.listar_citas, name='listar_citas'),
    path('detalle/<str:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('estado/<str:estado_filtro>/', views.filtrar_citas, name='filtrar_citas'),
    path('agendar/', views.agendar_cita, name='crear_cita'),
    path('editar/<str:cita_id>/', views.actualizar_cita, name='actualizar_cita'),
    path('eliminar/<str:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
]
