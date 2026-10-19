import os
import secrets

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from hub.catalog import CONTENT
from hub.models import (
    TRUE_FALSE_OPTIONS,
    Assessment,
    LearningPath,
    Lesson,
    LessonCheck,
    Question,
    Resource,
    ResourceVersion,
)

LANDINGS = {'Guía de pruebas batch y JCL': 'fundamentals', 'Checklist de pruebas de API REST': 'advanced'}


QUESTION_TOPICS = {
    '¿Qué evidencia demuestra la integridad del procesamiento?': 'Evidencia y conciliación',
    '¿Qué debe incluir un defecto reproducible?': 'Defectos',
    '¿Qué objetivo tiene una prueba negativa?': 'Pruebas negativas',
}
CREDENTIALS_FILE = 'demo-credentials.txt'
RESOURCE_TAGS = {
    'Guía de pruebas batch y JCL': 'jcl, batch, mainframe',
    'Checklist de pruebas de API REST': 'api, rest, distribuido',
    'Introducción a DB2 para QA': 'db2, mainframe',
    'Automatización de servicios con Python': 'api, python, automatizacion',
    'Documentación de Django': 'django, python',
    'Centro de documentación z/OS': 'mainframe, zos',
}
RELATED_RESOURCES = [
    ('Guía de pruebas batch y JCL', 'Introducción a DB2 para QA'),
    ('Checklist de pruebas de API REST', 'Automatización de servicios con Python'),
]
PRACTICE_QUESTIONS = [
    {
        'kind': 'single',
        'text': '¿Qué tipo de prueba verifica rápido que las funciones críticas funcionan?',
        'options': ['Smoke', 'Carga', 'Estilo'],
        'correct': 0,
        'explanation': 'La prueba smoke es una comprobación breve de las funciones críticas.',
        'topic': 'Tipos de prueba',
    },
    {
        'kind': 'multiple',
        'text': 'Selecciona los elementos de un defecto reproducible.',
        'options': [
            'Pasos para reproducir',
            'Datos de prueba',
            'Una opinión personal',
            'Resultado esperado y observado',
        ],
        'correct_set': [0, 1, 3],
        'explanation': 'Pasos, datos y resultados permiten a otra persona reproducir y verificar el defecto.',
        'topic': 'Defectos',
    },
    {
        'kind': 'truefalse',
        'text': 'Un RC=0 por sí solo demuestra que el proceso batch procesó todo correctamente.',
        'options': TRUE_FALSE_OPTIONS,
        'correct': 1,
        'explanation': 'Hay que conciliar entradas, salidas y rechazos; el código de retorno no basta.',
        'topic': 'Batch',
    },
    {
        'kind': 'short',
        'text': '¿Cómo se llaman las pruebas que detectan efectos adversos de un cambio?',
        'accepted': ['regresión', 'pruebas de regresión'],
        'explanation': 'Las pruebas de regresión comprueban que lo que ya funcionaba sigue funcionando.',
        'topic': 'Tipos de prueba',
    },
]


def read_credentials(path):
    if not path.exists():
        return {}
    return dict(line.split(': ', 1) for line in path.read_text(encoding='utf-8').splitlines() if ': ' in line)


class Command(BaseCommand):
    help = 'Carga datos ficticios. Idempotente; nunca usar en producción.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            help='Contraseña común para las cuentas demo nuevas (también DEMO_PASSWORD). Sin ella se generan aleatorias.',
        )
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Genera contraseñas nuevas para las cuentas demo que ya existen.',
        )

    def handle(self, *args, **options):
        fixed = options['password'] or os.environ.get('DEMO_PASSWORD')
        credentials_path = settings.BASE_DIR / CREDENTIALS_FILE
        issued = {}
        roles = {
            'Participante': [],
            'Editor': [
                'view_resource',
                'add_resource',
                'change_resource',
                'view_resourceversion',
                'add_resourceversion',
                'change_resourceversion',
                'view_learningpath',
                'add_learningpath',
                'change_learningpath',
                'view_lesson',
                'add_lesson',
                'change_lesson',
                'view_courseweek',
                'add_courseweek',
                'change_courseweek',
            ],
            'Evaluador': [
                'view_question',
                'add_question',
                'change_question',
                'delete_question',
                'view_assessment',
                'add_assessment',
                'change_assessment',
                'view_audit',
            ],
            'Administrador': list(Permission.objects.values_list('codename', flat=True)),
        }
        for name, codes in roles.items():
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(codename__in=codes))
        for username, first, last, role in [
            ('admin', 'Carlos', 'Demo', 'Administrador'),
            ('ana', 'Ana', 'Torres', 'Participante'),
            ('diego', 'Diego', 'Ramos', 'Editor'),
            ('lucia', 'Lucía', 'Vega', 'Evaluador'),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'is_staff': role != 'Participante',
                    'is_superuser': username == 'admin',
                },
            )
            if created or options['reset_passwords']:
                password = fixed or secrets.token_urlsafe(12)
                user.set_password(password)
                user.save()
                if not fixed:
                    issued[username] = password
            user.groups.add(Group.objects.get(name=role))
        resources = [
            (
                'Guía de pruebas batch y JCL',
                'Mainframe',
                'Documento',
                'Diseña una estrategia de validación batch: revisa condiciones de ejecución, códigos de retorno, datasets de entrada y salida y reconciliación de totales.\nEjercicio: define evidencias para un job que procesa 1.000 registros, rechaza 20 y genera 980 resultados.',
                '',
            ),
            (
                'Checklist de pruebas de API REST',
                'Distribuido',
                'Documento',
                'Planifica casos positivos y negativos, autenticación, contratos, idempotencia y manejo de errores. Ejercicio: verifica que una solicitud no autorizada no altere el estado del sistema.',
                '',
            ),
            (
                'Introducción a DB2 para QA',
                'Mainframe',
                'Video',
                'Sesión de referencia: consultas, integridad y comparación de resultados. El recurso enlazado es documentación pública de IBM, no una grabación incluida.',
                'https://www.ibm.com/docs/en/db2-for-zos',
            ),
            (
                'Automatización de servicios con Python',
                'Distribuido',
                'Video',
                'Guion de práctica: organiza datos, ejecuta solicitudes y compara resultados esperados. El enlace abre documentación de Python; el video debe cargarse en una fase posterior.',
                'https://docs.python.org/3/',
            ),
            (
                'Documentación de Django',
                'Distribuido',
                'Enlace',
                'Consulta oficial para modelos, autenticación, vistas y pruebas.',
                'https://docs.djangoproject.com/',
            ),
            (
                'Centro de documentación z/OS',
                'Mainframe',
                'Enlace',
                'Punto de consulta oficial para procesos y herramientas del entorno z/OS.',
                'https://www.ibm.com/docs/en/zos',
            ),
        ]
        for title, area, kind, description, url in resources:
            r, _ = Resource.objects.get_or_create(
                title=title, defaults=dict(area=area, kind=kind, description=description, url=url)
            )
            if title in LANDINGS and r.landing != LANDINGS[title]:
                r.landing = LANDINGS[title]
                r.save(update_fields=['landing'])
            for number, notes in [
                (1, 'Publicación inicial revisada por QA.'),
                (2, 'Incluye escenarios negativos y criterios de evidencia.'),
            ]:
                v, created = ResourceVersion.objects.get_or_create(resource=r, number=number, defaults={'notes': notes})
                if created and kind == 'Documento':
                    v.file.save(
                        f'guia-{r.pk}-v{number}.txt',
                        ContentFile((title + '\n\n' + description + '\n\n' + notes).encode('utf-8')),
                    )
        for area, title in [('Mainframe', 'Fundamentos QA Mainframe'), ('Distribuido', 'QA de servicios distribuidos')]:
            path, _ = LearningPath.objects.get_or_create(
                title=title,
                defaults={'area': area, 'description': 'Aprende con escenarios prácticos y evidencia verificable.'},
            )
            topics = [
                (
                    'Diseñar una estrategia de pruebas',
                    'Identifica riesgos, dependencias y criterios de aceptación.\nPráctica: enumera tres fallos que impidan procesar una transacción y define cómo detectarlos.',
                ),
                (
                    'Preparar datos y evidencias',
                    'Crea datos sintéticos reproducibles y conserva valores esperados.\nMainframe: concilia conteos y códigos de retorno. Distribuido: valida contrato, estado y efectos persistidos.',
                ),
                (
                    'Validar y comunicar resultados',
                    'Compara resultados observados con lo esperado. Documenta pasos, datos, evidencia y severidad.\nPráctica: redacta un defecto que otro profesional pueda reproducir.',
                ),
            ]
            for n, (t, b) in enumerate(topics, 1):
                Lesson.objects.get_or_create(path=path, position=n, defaults={'title': t, 'body': b})
            assessment, _ = Assessment.objects.get_or_create(title=title, defaults={'area': area})
            if not assessment.questions.exists():
                questions = [
                    (
                        '¿Qué evidencia demuestra la integridad del procesamiento?',
                        [
                            'Conciliación de entradas, salidas y rechazos',
                            'Solo una captura del inicio',
                            'El nombre del archivo',
                        ],
                        0,
                        'La conciliación permite explicar el destino de cada registro.',
                    ),
                    (
                        '¿Qué debe incluir un defecto reproducible?',
                        ['Solo la severidad', 'Pasos, datos, resultado esperado y observado', 'Una opinión general'],
                        1,
                        'Los pasos y datos hacen posible reproducir y verificar el defecto.',
                    ),
                    (
                        '¿Qué objetivo tiene una prueba negativa?',
                        [
                            'Evaluar entradas inválidas y manejo de errores',
                            'Duplicar los casos exitosos',
                            'Omitir validaciones',
                        ],
                        0,
                        'Debe comprobarse un rechazo controlado sin efectos indebidos.',
                    ),
                ]
                for text, options, correct, explanation in questions:
                    Question.objects.create(
                        assessment=assessment, text=text, options=options, correct=correct, explanation=explanation
                    )
        for slug, _label, area, title, body in CONTENT:
            Resource.objects.update_or_create(
                title=title, defaults={'area': area, 'kind': slug, 'description': body, 'published': True}
            )
        path, _ = LearningPath.objects.get_or_create(
            title='Academia CICC: certificación integral',
            defaults={
                'area': 'Transversal',
                'description': 'Desde el ambiente y los componentes hasta la evidencia y los incidentes.',
            },
        )
        for position, (_, _, _, title, body) in enumerate(CONTENT[:10], 1):
            Lesson.objects.update_or_create(path=path, position=position, defaults={'title': title, 'body': body})
        for title, tags in RESOURCE_TAGS.items():
            Resource.objects.filter(title=title, tags='').update(tags=tags)
        for first, second in RELATED_RESOURCES:
            a, b = Resource.objects.filter(title=first).first(), Resource.objects.filter(title=second).first()
            if a and b:
                a.related.add(b)
        lesson = Lesson.objects.filter(path__title='Academia CICC: certificación integral', position=2).first()
        if lesson and not lesson.checks.exists():
            LessonCheck.objects.create(
                lesson=lesson,
                text='¿Qué conviene registrar antes de ejecutar pruebas en un ambiente de certificación?',
                options=[
                    'Versión, configuración y datos sintéticos',
                    'Solo el nombre del analista',
                    'Nada: se documenta al final',
                ],
                correct=0,
                explanation='Un ambiente reproducible exige conocer la versión, la configuración y los datos usados.',
            )
        practice, _ = Assessment.objects.get_or_create(
            title='Práctica: tipos de pregunta', defaults={'area': 'Transversal', 'minutes': 10, 'pass_score': 60}
        )
        if not practice.questions.exists():
            for data in PRACTICE_QUESTIONS:
                Question.objects.create(assessment=practice, **data)
        for text, topic in QUESTION_TOPICS.items():
            Question.objects.filter(text=text, topic='').update(topic=topic)
        if issued:
            known = read_credentials(credentials_path)
            known.update(issued)
            header = '# Cuentas de demostración generadas por seed_demo. No lo subas a un repositorio.\n'
            body = ''.join(f'{name}: {password}\n' for name, password in known.items())
            credentials_path.write_text(header + body, encoding='utf-8')
        self.stdout.write(self.style.SUCCESS('Datos demo disponibles: admin, ana, diego, lucia.'))
        if issued:
            self.stdout.write(f'Contraseñas nuevas guardadas en {CREDENTIALS_FILE} ({len(issued)} cuentas).')
        elif fixed:
            self.stdout.write('Cuentas nuevas creadas con la contraseña indicada.')
