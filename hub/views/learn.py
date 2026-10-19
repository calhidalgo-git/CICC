"""Biblioteca de cursos semanales, fichas de recursos, favoritos, descargas y lecciones."""

import mimetypes
import os
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Max
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ..forms import ResourceVersionForm
from ..models import CourseWeek, Favorite, Lesson, Progress, Resource, ResourceVersion, WeekProgress
from .common import ctx, log, short_titles

QA_WEEKS = [
    'Semana 1 – Introducción al QA',
    'Semana 2 – Pruebas Manuales',
    'Semana 3 – Herramientas de QA',
    'Semana 4 – Automatización inicial',
    'Semana 5 – QA en metodologías ágiles y tradicionales',
    'Semana 6 – Tendencias y futuro del QA',
]
QA_ADVANCED_WEEKS = [
    'Semana 1 – Estrategias de pruebas avanzadas',
    'Semana 2 – Automatización intermedia',
    'Semana 3 – QA en CI/CD y DevOps',
    'Semana 4 – Testing basado en datos e IA',
    'Semana 5 – QA en metodologías híbridas',
    'Semana 6 – QA en pruebas de seguridad',
    'Semana 7 – QA en pruebas de rendimiento',
    'Semana 8 – QA en pruebas móviles',
    'Semana 9 – QA en pruebas de APIs y microservicios',
    'Semana 10 – QA en pruebas de accesibilidad y usabilidad',
    'Semana 11 – Soft skills y rol estratégico del QA',
]

# Cada curso semanal comparte las mismas dos pantallas: portada y detalle de semana.
COURSES = {
    'fundamentals': {
        'weeks': QA_WEEKS,
        'cover': 'fundamentals.html',
        'url_prefix': 'qa_fundamentals',
        'week_url': 'qa_week',
        'name': 'Fundamentos QA',
        'cover_path': 'qa/fundamentos',
        'template_dir': 'qa_weeks',
    },
    'advanced': {
        'weeks': QA_ADVANCED_WEEKS,
        'cover': 'qa_advanced.html',
        'url_prefix': 'qa_advanced',
        'week_url': 'qa_advanced_week',
        'name': 'QA Avanzado y Especialización',
        'cover_path': 'qa/avanzado',
        'template_dir': 'qa_advanced_weeks',
    },
}


def weeks_done(user, key):
    return set(WeekProgress.objects.filter(user=user, course=key).values_list('number', flat=True))


def course_cover(request, key):
    course = COURSES[key]
    titles = short_titles(course['weeks'])
    done = weeks_done(request.user, key)
    custom = {w.number: w.title for w in CourseWeek.objects.filter(course=key) if w.title}
    rows = [{'number': n, 'title': custom.get(n, t), 'done': n in done} for n, t in enumerate(titles, 1)]
    return render(
        request,
        course['cover'],
        ctx(request, 'library', weeks=titles, week_rows=rows, done_count=len(done & set(range(1, len(titles) + 1)))),
    )


def course_week(request, key, week):
    course = COURSES[key]
    total = len(course['weeks'])
    if not 1 <= week <= total:
        raise Http404
    done = weeks_done(request.user, key)
    db_week = CourseWeek.objects.filter(course=key, number=week).first()
    week_title = db_week.title if db_week and db_week.title else course['weeks'][week - 1]
    return render(
        request,
        'course_week.html',
        ctx(
            request,
            'library',
            course=course,
            course_key=key,
            week=week,
            total_weeks=total,
            week_title=week_title,
            weeks=short_titles(course['weeks']),
            weeks_done=done,
            week_done=week in done,
            db_week=db_week,
            week_template=f'{course["template_dir"]}/week_{week}.html',
            prev_week=week - 1 if week > 1 else None,
            next_week=week + 1 if week < total else None,
        ),
    )


@login_required
def qa_fundamentals(request):
    return course_cover(request, 'fundamentals')


@login_required
def qa_advanced(request):
    return course_cover(request, 'advanced')


@login_required
def qa_week(request, week):
    return course_week(request, 'fundamentals', week)


@login_required
def qa_advanced_week(request, week):
    return course_week(request, 'advanced', week)


@login_required
@require_POST
def toggle_week(request, course, week):
    if course not in COURSES or not 1 <= week <= len(COURSES[course]['weeks']):
        raise Http404
    progress, created = WeekProgress.objects.get_or_create(user=request.user, course=course, number=week)
    if not created:
        progress.delete()
    messages.success(request, f'Semana {week} {"marcada como completada" if created else "desmarcada"}.')
    url_name = COURSES[course]['week_url']
    return redirect(url_name, week=week)


def remember_recent(request, pk, limit=6):
    recent = [p for p in request.session.get('recent', []) if p != pk]
    request.session['recent'] = [pk, *recent][:limit]


@login_required
def resource(request, pk):
    item = get_object_or_404(Resource, pk=pk, published=True)
    remember_recent(request, item.pk)
    if item.landing in COURSES:
        return course_cover(request, item.landing)
    versions = list(item.versions.order_by('-number'))
    related = list(item.related.filter(published=True)[:4])
    if not related and item.tag_list:
        # Sin relaciones explícitas se sugieren recursos que comparten alguna etiqueta.
        pattern = r'(^|,\s*)(' + '|'.join(re.escape(t) for t in item.tag_list) + r')\s*(,|$)'
        related = list(Resource.objects.filter(published=True, tags__iregex=pattern).exclude(pk=item.pk)[:4])
    return render(
        request,
        'resource.html',
        ctx(
            request,
            'library',
            resource=item,
            versions=versions,
            player=next((v for v in versions if v.is_video), None),
            related=related,
            upload_form=ResourceVersionForm() if request.user.has_perm('hub.add_resourceversion') else None,
            is_favorite=Favorite.objects.filter(user=request.user, resource=item).exists(),
        ),
    )


@permission_required('hub.add_resourceversion', raise_exception=True)
@require_POST
def upload_version(request, pk):
    """Sube una versión nueva (documento o video) con validación de tipo y tamaño, sin pasar por Django Admin."""
    item = get_object_or_404(Resource, pk=pk)
    form = ResourceVersionForm(request.POST, request.FILES)
    if form.is_valid():
        version = form.save(commit=False)
        version.resource = item
        version.number = (item.versions.aggregate(last=Max('number'))['last'] or 0) + 1
        version.save()
        log(request.user, f'Sube versión {version.number} del recurso {item.pk}')
        messages.success(request, f'Se publicó la versión {version.number} de «{item.title}».')
    else:
        problems = '; '.join(m for errors in form.errors.values() for m in errors)
        messages.error(request, f'No se subió el archivo: {problems}')
    return redirect(f'/resource/{item.pk}/')


@login_required
@require_POST
def toggle_favorite(request, pk):
    item = get_object_or_404(Resource, pk=pk, published=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, resource=item)
    if not created:
        favorite.delete()
    messages.success(request, f'«{item.title}» {"se añadió a" if created else "se quitó de"} tus favoritos.')
    target = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        target = f'/resource/{item.pk}/'
    return redirect(target)


@login_required
def download(request, pk):
    version = get_object_or_404(ResourceVersion, pk=pk, resource__published=True)
    if not version.file:
        raise Http404
    log(request.user, f'Descarga recurso {version.resource_id} versión {version.number}')
    return FileResponse(version.file.open('rb'), as_attachment=True)


@login_required
@require_POST
def complete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    checks = list(lesson.checks.all())
    if checks and not Progress.objects.filter(user=request.user, lesson=lesson).exists():
        failed = []
        for check in checks:
            raw = request.POST.get(f'check-{check.pk}', '')
            if not (raw.isdigit() and int(raw) == check.correct):
                failed.append(check)
        if failed:
            detail = ' '.join(f'«{c.text}»: {c.explanation}' if c.explanation else f'«{c.text}»' for c in failed)
            messages.error(
                request,
                f'Todavía no: revisa {"esta pregunta" if len(failed) == 1 else f"estas {len(failed)} preguntas"} e inténtalo de nuevo. {detail}',
            )
            return redirect(f'/p/lessons/#lesson-{lesson.pk}')
    Progress.objects.get_or_create(user=request.user, lesson=lesson)
    done = set(Progress.objects.filter(user=request.user, lesson__path=lesson.path).values_list('lesson_id', flat=True))
    pending = [item for item in lesson.path.lessons.all() if item.pk not in done]
    # Sigue con la siguiente lección pendiente de la ruta; si no hay, celebra el cierre.
    upcoming = next((item for item in pending if item.position > lesson.position), None) or next(iter(pending), None)
    if upcoming:
        return redirect(f'/p/lessons/#lesson-{upcoming.pk}')
    messages.success(request, f'¡Completaste la ruta «{lesson.path.title}»!')
    return redirect(f'/p/lessons/#lesson-{lesson.pk}')


RANGE_RE = re.compile(r'^bytes=(\d*)-(\d*)$')
CHUNK = 64 * 1024


def read_range(path, start, length):
    with open(path, 'rb') as handle:
        handle.seek(start)
        while length > 0:
            data = handle.read(min(CHUNK, length))
            if not data:
                break
            length -= len(data)
            yield data


@login_required
def stream(request, pk):
    """Reproducción de video protegida con soporte de rangos, para poder avanzar y retroceder en el reproductor."""
    version = get_object_or_404(ResourceVersion, pk=pk, resource__published=True)
    if not version.is_video:
        raise Http404
    path = version.file.path
    size = os.path.getsize(path)
    content_type = mimetypes.guess_type(path)[0] or 'video/mp4'
    match = RANGE_RE.match(request.headers.get('Range', ''))
    if not match or match.group(0) == 'bytes=-':
        response = FileResponse(open(path, 'rb'), content_type=content_type)
        response['Accept-Ranges'] = 'bytes'
        return response
    first, last = match.groups()
    if first == '':  # «bytes=-N»: los últimos N bytes
        start, end = max(size - int(last), 0), size - 1
    else:
        start, end = int(first), min(int(last), size - 1) if last else size - 1
    if start >= size or start > end:
        response = HttpResponse(status=416)
        response['Content-Range'] = f'bytes */{size}'
        return response
    length = end - start + 1
    response = StreamingHttpResponse(read_range(path, start, length), status=206, content_type=content_type)
    response['Content-Range'] = f'bytes {start}-{end}/{size}'
    response['Content-Length'] = str(length)
    response['Accept-Ranges'] = 'bytes'
    return response
