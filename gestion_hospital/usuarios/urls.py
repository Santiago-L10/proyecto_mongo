from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.panel_home, name="panel_home"),
    # Perfiles / roles
    path("perfiles/", views.perfil_lista, name="perfil_lista"),
    path("perfiles/<str:perfil_id>/editar/", views.perfil_editar, name="perfil_editar"),
    # Usuarios
    path("usuarios/", views.usuario_lista, name="usuario_lista"),
    path("usuarios/crear/", views.usuario_crear, name="usuario_crear"),
    path(
        "usuarios/crear/<str:rol_nombre>/",
        views.usuario_crear_datos,
        name="usuario_crear_datos",
    ),
    path(
        "usuarios/<str:usuario_id>/eliminar/",
        views.usuario_eliminar,
        name="usuario_eliminar",
    ),
]
