"""Utilidades compartidas por las vistas."""

from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import F
from django.utils import timezone
from django.utils.dateparse import parse_date

from ..models import Attempt, Audit
from ..navigation import TITLES, groups_for
from ..services import log

PAGE_SIZE = 18
__all__ = [
    'filtered_audit',
    'PAGE_SIZE',
    'ctx',
    'deadline_for',
    'filtered_attempts',
    'is_expired',
    'log',
    'paginate',
    'passed',
    'querystring',
    'short_titles',
    'url_with',
]


def ctx(request, section, **extra):
    """Contexto común: menú agrupado según permisos, sección activa e intentos en curso."""
    return {
        'nav_groups': groups_for(request.user, section),
        'section': section,
        'title': TITLES.get(section, 'Recurso'),
        'active_attempts': Attempt.objects.filter(user=request.user, finished=False).count(),
        **extra,
    }


def paginate(request, queryset, size=PAGE_SIZE):
    return Paginator(queryset, size).get_page(request.GET.get('page'))


def url_with(request, **changes):
    """Query string actual con cambios aplicados (valor vacío o None elimina el parámetro). Reinicia la página."""
    params = request.GET.copy()
    params.pop('page', None)
    for key, value in changes.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f'?{encoded}' if encoded else '?'


def querystring(request, *drop):
    params = request.GET.copy()
    for key in ('page', *drop):
        params.pop(key, None)
    return params.urlencode()


def short_titles(weeks):
    return [title.split(' – ', 1)[-1] for title in weeks]


def filtered_attempts(params):
    """Intentos finalizados filtrados por usuario, evaluación y rango de fechas (parámetros GET)."""
    attempts = Attempt.objects.filter(finished=True).select_related('user', 'assessment').order_by('-started', '-pk')
    if params.get('usuario', '').isdigit():
        attempts = attempts.filter(user_id=int(params['usuario']))
    if params.get('evaluacion', '').isdigit():
        attempts = attempts.filter(assessment_id=int(params['evaluacion']))
    for key, lookup in (('desde', 'started__date__gte'), ('hasta', 'started__date__lte')):
        try:
            value = parse_date(params.get(key, ''))
        except ValueError:
            value = None
        if value:
            attempts = attempts.filter(**{lookup: value})
    return attempts


def filtered_audit(params):
    """Eventos de auditoría filtrados por texto, usuario y rango de fechas (parámetros GET)."""
    events = Audit.objects.select_related('user').order_by('-created', '-pk')
    text = params.get('q', '').strip()
    if text:
        events = events.filter(action__icontains=text)
    if params.get('usuario', '').isdigit():
        events = events.filter(user_id=int(params['usuario']))
    for key, lookup in (('desde', 'created__date__gte'), ('hasta', 'created__date__lte')):
        try:
            value = parse_date(params.get(key, ''))
        except ValueError:
            value = None
        if value:
            events = events.filter(**{lookup: value})
    return events


def passed(attempts):
    return attempts.filter(score__gte=F('assessment__pass_score'))


def is_expired(attempt):
    return timezone.now() >= attempt.deadline


def deadline_for(assessment):
    return timezone.now() + timedelta(minutes=assessment.minutes)
