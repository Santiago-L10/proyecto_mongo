from . import models

DESCRIPCIONES = {
    "ADMIN": "Acceso total al sistema.",
    "DOCTOR": "Gestión de citas e historiales médicos.",
    "PACIENTE": "Acceso a sus citas.",
    "FARMACEUTICO": "Gestión de farmacia y recetas.",
    "RECEPCIONISTA": "Gestión de citas y facturación.",
}


def crear_roles_iniciales(sender, **kwargs):
    for codigo, etiqueta in models.Rol.Nombre.choices:
        models.Perfil.objects.get_or_create(
            nombre=codigo,
            defaults={
                "descripcion": DESCRIPCIONES.get(codigo, ""),
                "activo": True,
            },
        )


#Crea el usuario administrador por defecto si no existe.
def crear_admin_inicial(sender, **kwargs):
    existe = models.User.objects.filter(email="admin@hospital.com").first()
    if existe is not None:
        return
    admin = models.User(
        first_name="Administrador",
        last_name="",
        email="admin@hospital.com",
        password="admin123",
        activo="SI",
        rol={"nombre": "ADMIN"},
    )
    admin.save()
