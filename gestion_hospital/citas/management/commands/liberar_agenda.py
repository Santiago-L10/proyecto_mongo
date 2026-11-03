from django.core.management.base import BaseCommand, CommandError

from citas.models import BloqueoAgenda


class Command(BaseCommand):
    help = 'Libera un bloqueo de agenda huérfano. Detén antes todos los procesos del servidor.'

    def add_arguments(self, parser):
        parser.add_argument('--token', required=True, help='Token exacto del bloqueo que se quiere liberar.')
        parser.add_argument('--servidor-detenido', action='store_true')

    def handle(self, *args, **options):
        if not options['servidor_detenido']:
            raise CommandError('Detén todos los procesos del servidor y usa --servidor-detenido para confirmar.')
        bloqueos = BloqueoAgenda.objects.filter(clave='agenda', token=options['token'])
        if not bloqueos.exists():
            raise CommandError('No existe un bloqueo con ese token; no se modificó la agenda.')
        bloqueos.delete()
        self.stdout.write(self.style.SUCCESS('Bloqueo liberado. Ya puedes iniciar el servidor.'))
