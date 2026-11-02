from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    name = 'usuarios'

    def ready(self):
        from django.db.models.signals import post_migrate

        from .seed import crear_roles_iniciales

        post_migrate.connect(
            crear_roles_iniciales,
            sender=self,
            dispatch_uid="usuarios_crear_roles_iniciales",
        )
