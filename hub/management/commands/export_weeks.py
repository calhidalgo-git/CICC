from django.core.management.base import BaseCommand
from django.template.loader import get_template

from hub.models import CourseWeek
from hub.views.learn import COURSES


class Command(BaseCommand):
    help = (
        'Copia el contenido de las semanas incluidas en el proyecto (plantillas HTML) a la base de datos '
        'para poder editarlas desde el administrador. No reemplaza semanas ya editadas salvo con --overwrite.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true', help='Reemplaza también las semanas ya guardadas.')

    def handle(self, *args, **options):
        created = updated = 0
        for key, course in COURSES.items():
            for number in range(1, len(course['weeks']) + 1):
                source = get_template(f'{course["template_dir"]}/week_{number}.html').template.source
                week, was_created = CourseWeek.objects.get_or_create(
                    course=key, number=number, defaults={'body': source}
                )
                if was_created:
                    created += 1
                elif options['overwrite']:
                    week.body = source
                    week.save(update_fields=['body'])
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f'Semanas creadas: {created}; actualizadas: {updated}'))
