import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .catalog import MODULES

AREA_CHOICES = [('Mainframe', 'Mainframe'), ('Distribuido', 'Distribuido'), ('Transversal', 'Transversal')]
KIND_CHOICES = [('Documento', 'Documento'), ('Video', 'Video'), ('Enlace', 'Enlace'), *MODULES.items()]
LANDING_CHOICES = [('fundamentals', 'Fundamentos QA'), ('advanced', 'QA Avanzado y Especialización')]
LANDING_TITLES = dict(LANDING_CHOICES)
VIDEO_EXTENSIONS = ('.mp4', '.webm', '.ogg')
UPLOAD_EXTENSIONS = [
    'pdf',
    'txt',
    'md',
    'csv',
    'docx',
    'xlsx',
    'pptx',
    'zip',
    'png',
    'jpg',
    'jpeg',
    'mp4',
    'webm',
    'ogg',
]
MAX_UPLOAD_MB = 200


def validate_upload_size(file):
    if file.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f'El archivo supera el máximo de {MAX_UPLOAD_MB} MB.')


COURSE_CHOICES = LANDING_CHOICES


class Resource(models.Model):
    title = models.CharField(max_length=200)
    area = models.CharField(max_length=20, choices=AREA_CHOICES)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='Documento')
    description = models.TextField()
    url = models.URLField(blank=True)
    published = models.BooleanField(default=True)
    landing = models.CharField(
        max_length=20,
        choices=LANDING_CHOICES,
        blank=True,
        help_text='Si se define, el recurso abre el curso semanal correspondiente en lugar de la ficha estándar.',
    )
    tags = models.CharField(
        max_length=200, blank=True, help_text='Etiquetas separadas por comas, por ejemplo: jcl, batch.'
    )
    related = models.ManyToManyField(
        'self', blank=True, help_text='Recursos que se muestran como «Ver también» (la relación es en ambos sentidos).'
    )

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    @property
    def display_kind(self):
        return MODULES.get(self.kind, self.kind)

    @property
    def display_title(self):
        return LANDING_TITLES.get(self.landing, self.title)

    def __str__(self):
        return self.title


class ResourceVersion(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='versions')
    number = models.PositiveIntegerField()
    notes = models.TextField()
    file = models.FileField(
        upload_to='resources/%Y/%m',
        blank=True,
        validators=[FileExtensionValidator(UPLOAD_EXTENSIONS), validate_upload_size],
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['resource', 'number'], name='unique_version')]

    @property
    def is_video(self):
        return bool(self.file) and self.file.name.lower().endswith(VIDEO_EXTENSIONS)


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='favorites')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'resource'], name='unique_favorite')]


class LearningPath(models.Model):
    title = models.CharField(max_length=200)
    area = models.CharField(max_length=20, choices=AREA_CHOICES)
    description = models.TextField()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    body = models.TextField()
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.title


class LessonCheck(models.Model):
    """Pregunta de comprobación de una lección. Si la lección tiene alguna, se debe acertar todo para completarla."""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='checks')
    text = models.TextField()
    options = models.JSONField(default=list)
    correct = models.PositiveSmallIntegerField(default=0, help_text='Índice (desde 0) de la opción correcta.')
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ['pk']

    def clean(self):
        if (
            not isinstance(self.options, list)
            or len(self.options) < 2
            or any(not isinstance(o, str) or not o.strip() for o in self.options)
        ):
            raise ValidationError({'options': 'Ingresa una lista JSON de al menos dos opciones de texto.'})
        if self.correct is None or not 0 <= self.correct < len(self.options):
            raise ValidationError({'correct': 'El índice debe corresponder a una opción, comenzando en cero.'})

    def __str__(self):
        return self.text[:80]


class Progress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'lesson'], name='unique_progress')]


class AssessmentQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Evaluaciones sin grupos asignados, las de los grupos del usuario, o todas para quien las administra."""
        if user.has_perm('hub.change_assessment'):
            return self
        return self.filter(Q(groups__isnull=True) | Q(groups__in=user.groups.all())).distinct()


class Assessment(models.Model):
    title = models.CharField(max_length=200)
    area = models.CharField(max_length=20, choices=AREA_CHOICES)
    minutes = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(240)])
    pass_score = models.PositiveIntegerField(default=70, validators=[MaxValueValidator(100)])
    max_attempts = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(50)],
        help_text='Intentos permitidos por persona. 0 significa sin límite.',
    )
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='assessments',
        help_text='Si eliges grupos, solo sus miembros ven y realizan la evaluación. Vacío = todos.',
    )
    questions_per_attempt = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(500)],
        help_text='Cuántas preguntas del banco recibe cada intento, repartidas entre los temas. 0 = todas.',
    )
    opens_at = models.DateTimeField(null=True, blank=True, help_text='Antes de esta fecha no se puede iniciar.')
    closes_at = models.DateTimeField(null=True, blank=True, help_text='Después de esta fecha no se puede iniciar.')

    objects = AssessmentQuerySet.as_manager()

    def availability(self, now=None):
        """None si se puede iniciar; si no, el motivo para mostrar al usuario."""
        now = now or timezone.now()
        if self.opens_at and now < self.opens_at:
            return f'Disponible desde el {timezone.localtime(self.opens_at):%d/%m/%Y %H:%M}'
        if self.closes_at and now > self.closes_at:
            return f'Cerrada desde el {timezone.localtime(self.closes_at):%d/%m/%Y %H:%M}'
        return None

    def __str__(self):
        return self.title


QUESTION_KINDS = [
    ('single', 'Selección única'),
    ('multiple', 'Selección múltiple'),
    ('truefalse', 'Verdadero / falso'),
    ('short', 'Respuesta corta'),
]
TRUE_FALSE_OPTIONS = ['Verdadero', 'Falso']


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    kind = models.CharField(max_length=10, choices=QUESTION_KINDS, default='single')
    text = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct = models.PositiveSmallIntegerField(default=0, help_text='Índice (desde 0) de la opción correcta.')
    correct_set = models.JSONField(default=list, blank=True, help_text='Selección múltiple: índices correctos.')
    accepted = models.JSONField(default=list, blank=True, help_text='Respuesta corta: respuestas aceptadas.')
    explanation = models.TextField()
    topic = models.CharField(max_length=80, blank=True, help_text='Tema para el desglose de resultados (opcional).')

    def clean(self):
        errors = {}
        has_options = isinstance(self.options, list) and all(isinstance(o, str) and o.strip() for o in self.options)
        if self.kind == 'short':
            accepted = self.accepted if isinstance(self.accepted, list) else []
            if not accepted or any(not isinstance(a, str) or not a.strip() for a in accepted):
                errors['accepted'] = 'Indica al menos una respuesta aceptada (lista de textos).'
        else:
            if not has_options or len(self.options) < 2:
                errors['options'] = 'Ingresa una lista JSON de al menos dos opciones de texto.'
            elif self.kind == 'truefalse' and self.options != TRUE_FALSE_OPTIONS:
                errors['options'] = 'Verdadero / falso usa exactamente las opciones Verdadero y Falso.'
            elif self.kind == 'multiple':
                chosen = self.correct_set if isinstance(self.correct_set, list) else []
                if (
                    not chosen
                    or len(set(chosen)) != len(chosen)
                    or any(type(i) is not int or not 0 <= i < len(self.options) for i in chosen)
                ):
                    errors['correct_set'] = 'Indica una o más opciones correctas, sin repetir y dentro del rango.'
            elif self.correct is None or not 0 <= self.correct < len(self.options):
                errors['correct'] = 'El índice debe corresponder a una opción, comenzando en cero.'
        if errors:
            raise ValidationError(errors)

    def as_snapshot(self):
        return {
            'id': self.pk,
            'kind': self.kind,
            'text': self.text,
            'options': list(self.options),
            'correct': self.correct,
            'correct_set': list(self.correct_set),
            'accepted': list(self.accepted),
            'explanation': self.explanation,
            'topic': self.topic,
        }

    def __str__(self):
        return self.text[:80]


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    started = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    answers = models.JSONField(default=dict)
    finished = models.BooleanField(default=False)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)
    updated = models.DateTimeField(auto_now=True)
    # Copia de las preguntas al iniciar: editar el banco no altera intentos en curso ni notas históricas.
    snapshot = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'assessment'],
                condition=Q(finished=False),
                name='one_active_attempt',
            )
        ]

    def frozen_questions(self):
        """Preguntas del intento. Los intentos anteriores a la instantánea usan el banco actual."""
        if self.snapshot:
            return self.snapshot
        return [q.as_snapshot() for q in self.assessment.questions.all()]

    @property
    def duration(self):
        return self.finished_at - self.started if self.finished_at else None


class Audit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)


class Certificate(models.Model):
    """Constancia de una evaluación aprobada. El código permite verificarla públicamente."""

    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name='certificate')
    code = models.CharField(max_length=20, unique=True, editable=False)
    issued = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        while not self.code:
            candidate = f'CICC-{secrets.token_hex(5).upper()}'
            if not Certificate.objects.filter(code=candidate).exists():
                self.code = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class CourseWeek(models.Model):
    """Contenido editable de una semana de curso. Si no existe, se usa la plantilla incluida en el proyecto."""

    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True, help_text='Opcional: reemplaza el título de la semana.')
    body = models.TextField(help_text='HTML del contenido. Solo editores de confianza deben modificarlo.')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['course', 'number'], name='unique_course_week')]
        ordering = ['course', 'number']

    def __str__(self):
        return f'{self.get_course_display()} · semana {self.number}'


class WeekProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    number = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'course', 'number'], name='unique_week_progress')]


class Notification(models.Model):
    """Registro de avisos enviados para no repetirlos (asignación de una evaluación, plazo próximo)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    sent = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'assessment', 'kind'], name='unique_notification')]
