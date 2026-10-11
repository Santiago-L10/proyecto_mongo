from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.panel_home, name="panel_home"),
    path("perfiles/", views.perfil_lista, name="perfil_lista"),
    path("perfiles/<str:perfil_id>/editar/", views.perfil_editar, name="perfil_editar"),
]
