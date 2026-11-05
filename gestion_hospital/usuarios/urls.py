from django.urls import path

from .views.viewAuth import login_sesion, logout_sesion
from .views.viewLog import log_lista
from .views.viewPanel import panel_home
from .views.viewRol import perfil_lista, perfil_editar
from .views.viewUsuario import (
    usuario_lista,
    usuario_crear,
    usuario_crear_datos,
    usuario_editar,
    usuario_eliminar,
)

app_name = "usuarios"

urlpatterns = [
    path("login/", login_sesion, name="login_sesion"),
    path("logout/", logout_sesion, name="logout_sesion"),
    path("", panel_home, name="panel_home"),
    path("logs/", log_lista, name="log_lista"),
    # Perfiles / roles
    path("perfiles/", perfil_lista, name="perfil_lista"),
    path("perfiles/<str:perfil_id>/editar/", perfil_editar, name="perfil_editar"),
    # Usuarios
    path("usuarios/", usuario_lista, name="usuario_lista"),
    path("usuarios/crear/", usuario_crear, name="usuario_crear"),
    path(
        "usuarios/crear/<str:rol_nombre>/",
        usuario_crear_datos,
        name="usuario_crear_datos",
    ),
    path(
        "usuarios/<str:usuario_id>/editar/",
        usuario_editar,
        name="usuario_editar",
    ),
    path(
        "usuarios/<str:usuario_id>/eliminar/",
        usuario_eliminar,
        name="usuario_eliminar",
    ),
]
