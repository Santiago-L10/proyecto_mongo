from bson import ObjectId
from bson.errors import InvalidId

from ..acceso import nombres_modulos, modulos_de


#Convierte el id recibido por la URL al tipo de dato que usa Mongo.
def paramToId(valor):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        return valor


#Mostrar el nombre de los modulos por perfil
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


#Devuelve el nombre del rol guardado en el usuario.
def nombre_rol(user):
    rol = user.rol
    if isinstance(rol, dict):
        return rol.get("nombre")
    return getattr(rol, "nombre", None)
