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

# Qué sección de datos extra se llena según el rol al registrar un usuario.
# Los roles que no aparezcan aquí no piden datos adicionales.
SECCION_POR_ROL = {
    "DOCTOR": "datos_profesionales",
    "FARMACEUTICO": "datos_profesionales",
    "PACIENTE": "antecedentes_clinicos",
}

# Lista de modulos por rol
def modulos_de(nombre_rol):
    return MODULOS_POR_ROL.get(nombre_rol, [])

# Confirmar si el usuario con rol ingresa al modulo
def puede_acceder(nombre_rol, modulo):
    return modulo in modulos_de(nombre_rol)

# Convierte códigos de módulo en sus nombres visibles
def nombres_modulos(codigos):
    nombres = []
    for codigo in codigos:
        nombres.append(MODULOS.get(codigo, codigo))
    return nombres
