from bson import ObjectId
from bson.errors import InvalidId

from ..acceso import nombres_modulos, modulos_de


def paramToId(valor):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        return valor


def perfiles_con_modulos(perfiles):
    resultado = []
    for perfil in perfiles:
        resultado.append(
            {
                "perfil": perfil,
                "modulos": nombres_modulos(modulos_de(perfil.nombre)),
            }
        )
    return resultado


def nombre_rol(user):
    rol = user.rol
    if isinstance(rol, dict):
        return rol.get("nombre")
    return getattr(rol, "nombre", None)
