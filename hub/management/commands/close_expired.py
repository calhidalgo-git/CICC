from django.core.management.base import BaseCommand
from django.utils import timezone

from hub.models import Attempt
from hub.services import close_if_expired


class Command(BaseCommand):
    help = (
        'Califica y cierra los intentos cuyo tiempo venció (envía el aviso por correo si la persona tiene uno). '
        'Pensado para ejecutarse cada pocos minutos con cron o el Programador de tareas de Windows.'
    )

    def handle(self, *args, **options):
        expired = Attempt.objects.filter(finished=False, deadline__lte=timezone.now()).select_related(
            'user', 'assessment'
        )
        closed = 0
        for attempt in expired:
            close_if_expired(attempt)
            closed += 1
        self.stdout.write(self.style.SUCCESS(f'Intentos vencidos cerrados: {closed}'))
