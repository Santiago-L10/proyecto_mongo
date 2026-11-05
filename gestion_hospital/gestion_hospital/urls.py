"""
URL configuration for gestion_hospital project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('usuarios.urls')),
    path('citas/', include('citas.urls')),
    path('registros_medicos/', include('registros_medicos.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('farmacia/', include('farmacia.urls')),
    # La entrada al sistema es el login; según el rol se redirige a su módulo.
    path('', lambda request: redirect('usuarios:login_sesion')),
]
