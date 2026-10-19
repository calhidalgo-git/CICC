"""Perfil de la persona: datos de contacto, progreso e historial."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from ..forms import ProfileForm
from ..models import Attempt, Certificate, WeekProgress
from .common import ctx, log
from .learn import COURSES
from .pages import path_progress


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log(request.user, 'Actualiza su perfil')
        messages.success(request, 'Tus datos se actualizaron.')
        return redirect('/cuenta/')
    rows, done = path_progress(request.user)
    week_counts = dict(
        WeekProgress.objects.filter(user=request.user)
        .values_list('course')
        .annotate(n=Count('pk'))
        .values_list('course', 'n')
    )
    attempts = (
        Attempt.objects.filter(user=request.user, finished=True).select_related('assessment').order_by('-started')
    )
    best = {}
    for attempt in attempts:
        best[attempt.assessment] = max(best.get(attempt.assessment, 0), attempt.score)
    return render(
        request,
        'profile.html',
        ctx(
            request,
            'account',
            title='Mi perfil',
            form=form,
            path_rows=rows,
            lessons_done=len(done),
            courses=[
                {'name': c['name'], 'done': min(week_counts.get(k, 0), len(c['weeks'])), 'total': len(c['weeks'])}
                for k, c in COURSES.items()
            ],
            recent_attempts=attempts[:6],
            attempt_total=attempts.count(),
            best_scores=[
                {'assessment': a, 'score': score, 'passed': score >= a.pass_score} for a, score in best.items()
            ],
            certificate_count=Certificate.objects.filter(attempt__user=request.user).count(),
        ),
    )
