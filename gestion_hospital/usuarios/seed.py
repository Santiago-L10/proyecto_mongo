from . import models

DESCRIPCIONES = {
    "ADMIN": "Acceso total al sistema.",
    "DOCTOR": "Gestión de citas e historiales médicos.",
    "PACIENTE": "Acceso a sus citas.",
    "FARMACEUTICO": "Gestión de farmacia y recetas.",
    "RECEPCIONISTA": "Gestión de citas y facturación.",
}


def crear_roles_iniciales(sender, **kwargs):
    for codigo in models.Rol.Nombre.choices:
        models.Perfil.objects.get_or_create(
            nombre=codigo,
            defaults={
                "descripcion": DESCRIPCIONES.get(codigo, ""),
                "activo": True,
            },
        )
