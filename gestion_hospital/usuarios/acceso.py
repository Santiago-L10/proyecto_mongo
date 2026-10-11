# Catálogo de módulos disponibles: código de la app -> nombre visible.
MODULOS = {
    "usuarios": "Usuarios",
    "citas": "Citas",
    "farmacia": "Farmacia",
    "facturacion": "Facturación",
    "registros_medicos": "Registros Médicos",
}

# A qué módulos puede entrar cada rol. Ajusta esta tabla a tu gusto.
MODULOS_POR_ROL = {
    "ADMIN": ["usuarios", "citas", "farmacia", "facturacion", "registros_medicos"],
    "DOCTOR": ["citas", "registros_medicos"],
    "PACIENTE": ["citas"],
    "FARMACEUTICO": ["farmacia"],
    "RECEPCIONISTA": ["citas", "facturacion"],
}

# Lista de modulos por rol
def modulos_de(nombre_rol):
    return MODULOS_POR_ROL.get(nombre_rol, [])

# Confirmar si el usuario con rol ingresa al modulo
def puede_acceder(nombre_rol, modulo):
    return modulo in modulos_de(nombre_rol)


def nombres_modulos(codigos):
    """Convierte códigos de módulo en sus nombres visibles."""
    return [MODULOS.get(codigo, codigo) for codigo in codigos]
