from django.core.management.base import BaseCommand

from hub.services import send_assessment_notices


class Command(BaseCommand):
    help = (
        'Envía por correo (una sola vez por persona) el aviso de evaluaciones asignadas a su grupo que ya están abiertas '
        'y el recordatorio de las que cierran en menos de 48 horas. Ejecútalo cada hora con cron o el Programador de tareas.'
    )

    def handle(self, *args, **options):
        assigned, closing = send_assessment_notices()
        self.stdout.write(self.style.SUCCESS(f'Avisos de asignación: {assigned}; recordatorios de cierre: {closing}'))
