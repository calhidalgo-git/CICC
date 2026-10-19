"""Páginas de navegación (/p/<sección>/). Cada sección calcula solo los datos que necesita."""

import re
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db import connection
from django.db.models import Avg, Count, F, Q
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from ..catalog import MODULES
from ..models import (
    Assessment,
    Attempt,
    Certificate,
    Favorite,
    LearningPath,
    Lesson,
    Progress,
    Question,
    Resource,
    WeekProgress,
)
from ..navigation import SLUGS, allowed
from ..services import is_correct
from .common import ctx, filtered_attempts, filtered_audit, paginate, passed, querystring, url_with
from .learn import COURSES

AREAS = ['Mainframe', 'Distribuido', 'Transversal']
KINDS = ['Documento', 'Video', 'Enlace']
SORTS = [('recientes', 'Más recientes'), ('titulo', 'Título (A–Z)')]


def path_progress(user):
    """Rutas con avance del usuario: total, completadas, porcentaje y próxima lección."""
    done = set(Progress.objects.filter(user=user).values_list('lesson_id', flat=True))
    rows = []
    for path in LearningPath.objects.prefetch_related('lessons__checks'):
        lessons = list(path.lessons.all())
        completed = sum(lesson.pk in done for lesson in lessons)
        rows.append(
            {
                'path': path,
                'lessons': lessons,
                'total': len(lessons),
                'done': completed,
                'pct': round(100 * completed / len(lessons)) if lessons else 0,
                'next': next((lesson for lesson in lessons if lesson.pk not in done), None),
            }
        )
    return rows, done


def dashboard(request, section):
    rows, done = path_progress(request.user)
    published = Resource.objects.filter(published=True)
    started = [row for row in rows if row['next'] and row['done']]
    next_row = (started or [row for row in rows if row['next']] or [None])[0]
    active_attempt = (
        Attempt.objects.filter(user=request.user, finished=False)
        .select_related('assessment')
        .order_by('-started')
        .first()
    )
    passed_ids = set(
        passed(Attempt.objects.filter(user=request.user, finished=True)).values_list('assessment_id', flat=True)
    )
    assessments = list(
        Assessment.objects.visible_to(request.user).annotate(question_count=Count('questions')).order_by('pk')
    )
    if active_attempt:
        recommended = next((a for a in assessments if a.pk == active_attempt.assessment_id), None)
    else:
        recommended = next((a for a in assessments if a.pk not in passed_ids), assessments[0] if assessments else None)
    week_counts = dict(
        WeekProgress.objects.filter(user=request.user)
        .values_list('course')
        .annotate(n=Count('pk'))
        .values_list('course', 'n')
    )
    course_rows = []
    for key, course in COURSES.items():
        total = len(course['weeks'])
        weeks_completed = min(week_counts.get(key, 0), total)
        course_rows.append(
            {
                'name': course['name'],
                'url': f'/{course["cover_path"]}/',
                'done': weeks_completed,
                'total': total,
                'pct': round(100 * weeks_completed / total),
            }
        )
    recent_ids = request.session.get('recent', [])
    recent = sorted(published.filter(pk__in=recent_ids), key=lambda r: recent_ids.index(r.pk))
    return 'dashboard', {
        'resource_count': published.count(),
        'progress_count': len(done),
        'lesson_count': sum(row['total'] for row in rows),
        'pending_lessons': sum(row['total'] - row['done'] for row in rows),
        'assessment_count': len(assessments),
        'area_count': published.exclude(area='Transversal').values('area').distinct().count(),
        'latest_resources': published.order_by('-pk')[:3],
        'path_rows': rows,
        'course_rows': course_rows,
        'next_row': next_row,
        'active_attempt': active_attempt,
        'recommended': recommended,
        'recent_resources': recent,
    }


def resource_list(request, section):
    """Biblioteca, videoteca, enlaces, favoritos, módulos temáticos y búsqueda global."""
    query = request.GET.get('q', '').strip()
    area = request.GET.get('area', '')
    kind = request.GET.get('tipo', '')
    tag = request.GET.get('etiqueta', '').strip()[:50]
    resources = Resource.objects.filter(published=True)
    if section in MODULES:
        resources = resources.filter(kind=section)
    elif section == 'videos':
        resources = resources.filter(kind='Video')
    elif section == 'links':
        resources = resources.filter(kind='Enlace')
    elif section == 'favorites':
        resources = resources.filter(favorites__user=request.user)
    elif section == 'library' and kind in KINDS:
        resources = resources.filter(kind=kind)
    if query:
        resources = resources.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(area__icontains=query)
        )
    elif section == 'search':
        resources = resources.none()
    if area in AREAS:
        resources = resources.filter(area=area)
    if tag:
        resources = resources.filter(tags__iregex=r'(^|,\s*)' + re.escape(tag) + r'\s*(,|$)')
    default_sort = 'titulo' if section in MODULES or section == 'search' else 'recientes'
    sort = request.GET.get('orden', default_sort)
    resources = resources.annotate(version_count=Count('versions', distinct=True))
    resources = resources.order_by('title' if sort == 'titulo' else '-pk')
    page = paginate(request, resources)

    extra = {}
    if section == 'search' and query:
        extra = {
            'search_lessons': Lesson.objects.filter(
                Q(title__icontains=query) | Q(body__icontains=query) | Q(path__title__icontains=query)
            ).select_related('path'),
            'search_paths': LearningPath.objects.filter(Q(title__icontains=query) | Q(description__icontains=query)),
            'search_assessments': Assessment.objects.filter(Q(title__icontains=query) | Q(area__icontains=query)),
        }
    favorite_ids = set(Favorite.objects.filter(user=request.user).values_list('resource_id', flat=True))
    return 'resources', {
        'resources': page,
        'page_obj': page,
        'querystring': querystring(request),
        'query': query,
        'area': area,
        'kind': kind,
        'tag': tag,
        'tag_clear_url': url_with(request, etiqueta=''),
        'sort': sort,
        'sorts': SORTS,
        'favorite_ids': favorite_ids,
        'area_chips': [
            {'label': label, 'url': url_with(request, area=value), 'active': area == value}
            for label, value in [('Todas', ''), *[(a, a) for a in AREAS]]
        ],
        'kind_chips': (
            [
                {'label': label, 'url': url_with(request, tipo=value), 'active': kind == value}
                for label, value in [('Todos los tipos', ''), *[(k, k) for k in KINDS]]
            ]
            if section == 'library'
            else []
        ),
        'module_section': section in MODULES,
        'show_filters': section != 'favorites' or page.paginator.count > 0,
        **extra,
    }


def components(request, section):
    return 'components', {}


def paths(request, section):
    rows, _ = path_progress(request.user)
    return 'paths', {'path_rows': rows}


def lessons(request, section):
    rows, done = path_progress(request.user)
    return 'lessons', {'path_rows': rows, 'done': done}


def assessments(request, section):
    attempts = defaultdict(list)
    for attempt in Attempt.objects.filter(user=request.user):
        attempts[attempt.assessment_id].append(attempt)
    cards = []
    for assessment in (
        Assessment.objects.visible_to(request.user).annotate(question_count=Count('questions')).order_by('pk')
    ):
        mine = attempts[assessment.pk]
        finished = [a for a in mine if a.finished]
        active = next((a for a in mine if not a.finished), None)
        best = max((a.score for a in finished), default=None)
        within_limit = not assessment.max_attempts or len(finished) < assessment.max_attempts
        closed_reason = None if active else assessment.availability()
        if active:
            label = 'Reanudar evaluación'
        elif finished:
            label = 'Reintentar evaluación'
        else:
            label = 'Iniciar evaluación'
        cards.append(
            {
                'assessment': assessment,
                'active': active,
                'best': best,
                'passed': best is not None and best >= assessment.pass_score,
                'attempts_used': len(finished),
                'can_start': bool(active) or (within_limit and assessment.question_count > 0 and not closed_reason),
                'blocked_reason': (
                    closed_reason
                    or (
                        'Sin preguntas disponibles'
                        if not assessment.question_count
                        else 'Alcanzaste el límite de intentos'
                    )
                ),
                'label': label,
            }
        )
    return 'assessments', {'cards': cards}


def results(request, section):
    finished = (
        Attempt.objects.filter(user=request.user, finished=True).select_related('assessment').order_by('-started')
    )
    return 'results', {'attempts': paginate(request, finished, 20), 'querystring': querystring(request)}


def questions(request, section):
    bank = Question.objects.select_related('assessment').order_by('assessment_id', 'pk')
    selected = request.GET.get('evaluacion', '')
    if selected.isdigit():
        bank = bank.filter(assessment_id=int(selected))
    return 'questions', {
        'questions': paginate(request, bank, 25),
        'querystring': querystring(request),
        'filter_assessments': Assessment.objects.order_by('title'),
        'selected_assessment': selected,
        'can_delete': request.user.has_perm('hub.delete_question'),
    }


def certificates(request, section):
    mine = (
        Certificate.objects.filter(attempt__user=request.user).select_related('attempt__assessment').order_by('-issued')
    )
    return 'certificates', {'certificates': paginate(request, mine, 12), 'querystring': querystring(request)}


def report_charts(attempts):
    """Aprobación por evaluación, preguntas más falladas y evolución de los últimos 30 días."""
    by_assessment = (
        attempts.values('assessment__title')
        .annotate(n=Count('pk'), avg=Avg('score'), ok=Count('pk', filter=Q(score__gte=F('assessment__pass_score'))))
        .order_by('assessment__title')
    )
    assessment_rows = [
        {
            'title': row['assessment__title'],
            'attempts': row['n'],
            'average': round(row['avg'] or 0, 1),
            'pass_rate': round(100 * row['ok'] / row['n']),
        }
        for row in by_assessment
    ]
    # Preguntas más falladas: se recorre una muestra acotada de intentos recientes con sus preguntas congeladas.
    stats = {}
    fallback = {}
    for attempt in attempts.select_related('assessment')[:500]:
        questions = attempt.snapshot or fallback.setdefault(
            attempt.assessment_id, [q.as_snapshot() for q in attempt.assessment.questions.all()]
        )
        for question in questions:
            entry = stats.setdefault(
                (attempt.assessment.title, question['id']),
                {'assessment': attempt.assessment.title, 'text': question['text'], 'answered': 0, 'ok': 0},
            )
            entry['answered'] += 1
            entry['ok'] += is_correct(question, attempt.answers.get(str(question['id'])))
    hardest = sorted(
        ({**e, 'pct': round(100 * e['ok'] / e['answered'])} for e in stats.values() if e['answered'] >= 1),
        key=lambda e: (e['pct'], -e['answered']),
    )[:8]
    since = timezone.now() - timedelta(days=29)
    daily = (
        attempts.filter(started__gte=since)
        .annotate(day=TruncDate('started'))
        .values('day')
        .annotate(n=Count('pk'), avg=Avg('score'))
        .order_by('day')
    )
    trend = [
        {'day': f'{row["day"]:%d/%m}', 'attempts': row['n'], 'average': round(row['avg'] or 0, 1)} for row in daily
    ]
    return assessment_rows, hardest, trend


def reports(request, section):
    attempts = filtered_attempts(request.GET)
    summary = attempts.aggregate(total=Count('pk'), average=Avg('score'))
    passed_count = passed(attempts).count()
    published = Resource.objects.filter(published=True)
    chart = [published.filter(area='Mainframe').count(), published.filter(area='Distribuido').count()]
    assessment_rows, hardest, trend = report_charts(attempts)
    return 'reports', {
        'chart_data': chart,
        'charts': {
            'pass': {
                'labels': [r['title'] for r in assessment_rows],
                'values': [r['pass_rate'] for r in assessment_rows],
            },
            'trend': {
                'labels': [t['day'] for t in trend],
                'attempts': [t['attempts'] for t in trend],
                'average': [t['average'] for t in trend],
            },
        },
        'assessment_rows': assessment_rows,
        'hardest': hardest,
        'trend': trend,
        'resource_count': published.count(),
        'assessment_count': Assessment.objects.count(),
        'user_count': User.objects.count(),
        'attempts': paginate(request, attempts, 20),
        'querystring': querystring(request),
        'export_query': request.GET.urlencode(),
        'summary': summary,
        'pass_rate': round(100 * passed_count / summary['total']) if summary['total'] else None,
        'filter_users': User.objects.order_by('username'),
        'filter_assessments': Assessment.objects.order_by('title'),
        'filters': {key: request.GET.get(key, '') for key in ('usuario', 'evaluacion', 'desde', 'hasta')},
    }


def users(request, section):
    team = User.objects.prefetch_related('groups').order_by('username')
    return 'users', {'users': paginate(request, team, 25), 'querystring': querystring(request)}


def roles(request, section):
    return 'roles', {'roles': Group.objects.prefetch_related('permissions__content_type')}


def settings_page(request, section):
    return 'settings', {'db_vendor': connection.vendor, 'time_zone': settings.TIME_ZONE, 'debug': settings.DEBUG}


def audit(request, section):
    events = filtered_audit(request.GET)
    return 'audit', {
        'audits': paginate(request, events, 50),
        'querystring': querystring(request),
        'export_query': request.GET.urlencode(),
        'filter_users': User.objects.order_by('username'),
        'filters': {key: request.GET.get(key, '') for key in ('q', 'usuario', 'desde', 'hasta')},
    }


def backups(request, section):
    return 'backups', {}


HANDLERS = {
    'dashboard': dashboard,
    'components': components,
    'paths': paths,
    'lessons': lessons,
    'assessments': assessments,
    'results': results,
    'certificates': certificates,
    'questions': questions,
    'reports': reports,
    'users': users,
    'roles': roles,
    'settings': settings_page,
    'audit': audit,
    'backups': backups,
}


@login_required
def page(request, section='dashboard'):
    if section not in SLUGS:
        raise Http404
    if not allowed(request.user, section):
        return HttpResponse('Acceso restringido por tu rol', status=403)
    handler = HANDLERS.get(section, resource_list)
    template, extra = handler(request, section)
    return render(request, 'page.html', ctx(request, section, section_template=f'sections/{template}.html', **extra))
