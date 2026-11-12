
MODULOS = {
    "usuarios": "Usuarios",
    "citas": "Citas",
    "farmacia": "Farmacia",
    "facturacion": "Facturación",
    "registros_medicos": "Registros Médicos",
}


MODULOS_POR_ROL = {
    "ADMIN": ["usuarios", "citas", "farmacia", "facturacion", "registros_medicos"],
    "DOCTOR": ["citas", "registros_medicos"],
    "PACIENTE": ["citas"],
    "FARMACEUTICO": ["farmacia"],
    "ADMINISTRATIVO": ["citas", "facturacion"],
}


SECCION_POR_ROL = {
    "DOCTOR": "datos_profesionales",
    "FARMACEUTICO": "datos_profesionales",
    "PACIENTE": "antecedentes_clinicos",
}

def modulos_de(nombre_rol):
    return MODULOS_POR_ROL.get(nombre_rol, [])


def puede_acceder(nombre_rol, modulo):
    return modulo in modulos_de(nombre_rol)


def nombres_modulos(codigos):
    nombres = []
    for codigo in codigos:
        nombres.append(MODULOS.get(codigo, codigo))
    return nombres
