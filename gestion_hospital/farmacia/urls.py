from django.urls import path
from . import views

app_name = 'farmacia'

urlpatterns = [
    path('homeFarm/', views.inicio, name='inicio'),

    path('medicamentos/', views.consultarMedicamentos, name='medicamentos'),
    path('medicamento/<int:id>/', views.consultarMedicamento, name='medicamento'),
    path('crearMedicamento/', views.crearMedicamento, name='crearMedicamento'),
    path('actualizarMedicamento/<int:id>/', views.actualizarMedicamento, name='actualizarMedicamento'),
    path('eliminarMedicamento/<int:id>/', views.eliminarMedicamento, name='eliminarMedicamento'),
]
