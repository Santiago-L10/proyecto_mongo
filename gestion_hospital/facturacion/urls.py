from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('homeFact/', views.inicio, name='inicio'),

    path('polizas/', views.consultarPolizas, name='polizas'),
    path('crearPoliza/', views.crearPoliza, name='crearPoliza'),
    path('actualizarPoliza/<int:id>/', views.actualizarPoliza, name='actualizarPoliza'),
    path('eliminarPoliza/<int:id>/', views.eliminarPoliza, name='eliminarPoliza'),

    path('titular/<int:id>/', views.consultarTitular, name='titular'),
    path('actualizarTitular/<int:id>/', views.actualizarTitular, name='actualizarTitular'),

    path('facturas/', views.consultarFacturas, name='facturas'),
    path('crearFactura/', views.crearFactura, name='crearFactura'),
    path('actualizarFactura/<int:id>/', views.actualizarFactura, name='actualizarFactura'),
    path('eliminarFactura/<int:id>/', views.eliminarFactura, name='eliminarFactura'),

    path('paciente/<int:id>/', views.consultarPaciente, name='paciente'),
    path('actualizarPaciente/<int:id>/', views.actualizarPaciente, name='actualizarPaciente'),

    path('items/<int:id>/', views.consultarItems, name='items'),
    path('crearItem/<int:id>/', views.crearItem, name='crearItem'),
    path('actualizarItem/<int:id>/<int:posicion>/', views.actualizarItem, name='actualizarItem'),
    path('eliminarItem/<int:id>/<int:posicion>/', views.eliminarItem, name='eliminarItem'),

    path('cobertura/<int:id>/', views.consultarCobertura, name='cobertura'),
    path('crearCobertura/<int:id>/', views.crearCobertura, name='crearCobertura'),
    path('actualizarCobertura/<int:id>/', views.actualizarCobertura, name='actualizarCobertura'),
    path('eliminarCobertura/<int:id>/', views.eliminarCobertura, name='eliminarCobertura'),
]
