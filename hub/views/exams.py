"""Evaluaciones: inicio, autoguardado, calificación y resultados."""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import Assessment, Attempt
from ..services import close_if_expired, draw_questions, grade, is_blank, is_correct, valid_answer
from .common import ctx, deadline_for, is_expired, log


@login_required
@require_POST
def start(request, pk):
    assessment = get_object_or_404(Assessment.objects.visible_to(request.user), pk=pk)
    questions = list(assessment.questions.all())
    if not questions:
        return HttpResponse('Evaluación sin preguntas', status=400)
    mine = Attempt.objects.filter(user=request.user, assessment=assessment)
    active = mine.filter(finished=False).first()
    if active and close_if_expired(active).finished:
        active = None
    if not active:
        closed_reason = assessment.availability()
        if closed_reason:
            messages.error(request, f'«{assessment.title}» no está disponible: {closed_reason}.')
            return redirect('/p/assessments/')
        if assessment.max_attempts and mine.filter(finished=True).count() >= assessment.max_attempts:
            messages.error(request, f'Alcanzaste el límite de {assessment.max_attempts} intentos para esta evaluación.')
            return redirect('/p/assessments/')
        questions = draw_questions(questions, assessment.questions_per_attempt)
        try:
            with transaction.atomic():
                active = Attempt.objects.create(
                    user=request.user,
                    assessment=assessment,
                    deadline=deadline_for(assessment),
                    snapshot=[q.as_snapshot() for q in questions],
                )
            log(request.user, f'Inicio evaluación {assessment.pk}')
        except IntegrityError:
            # Otra petición simultánea ya abrió el intento: se reutiliza.
            active = mine.get(finished=False)
    return redirect('exam', pk=active.pk)


@login_required
def exam(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
    close_if_expired(attempt)
    if attempt.finished:
        return redirect('results', pk=attempt.pk)
    # El enunciado y las opciones viajan al navegador; la respuesta correcta y la explicación no.
    questions = [
        {'id': q['id'], 'kind': q.get('kind', 'single'), 'text': q['text'], 'options': q['options']}
        for q in attempt.frozen_questions()
    ]
    return render(
        request,
        'exam.html',
        ctx(
            request,
            'assessments',
            attempt=attempt,
            exam_questions=questions,
            deadline=attempt.deadline.isoformat(),
            server_now=timezone.now().isoformat(),
        ),
    )


@login_required
@require_POST
@transaction.atomic
def save(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_for_update(), pk=pk, user=request.user)
    if attempt.finished:
        return JsonResponse({'error': 'Intento cerrado'}, status=409)
    if is_expired(attempt):
        grade(attempt)
        return JsonResponse({'expired': True}, status=409)
    try:
        data = json.loads(request.body)
        questions = {str(q['id']): q for q in attempt.frozen_questions()}
        valid = isinstance(data, dict) and all(
            key in questions and valid_answer(questions[key], value) for key, value in data.items()
        )
        if not valid:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Respuestas inválidas'}, status=400)
    attempt.answers = data
    attempt.save()
    return JsonResponse({'saved': True, 'at': timezone.now().isoformat()})


@login_required
@require_POST
@transaction.atomic
def finish(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_for_update(), pk=pk, user=request.user)
    if not attempt.finished:
        grade(attempt)
        log(request.user, f'Finaliza evaluación {attempt.pk}: {attempt.score}%')
    return redirect('results', pk=attempt.pk)


def review_row(question, answer):
    """Datos para mostrar una pregunta revisada: estado, opciones marcadas y, en respuesta corta, lo escrito y lo aceptado."""
    kind = question.get('kind', 'single')
    status = 'blank' if is_blank(answer) else 'ok' if is_correct(question, answer) else 'wrong'
    row = {'question': question, 'kind': kind, 'status': status, 'options': [], 'given': '', 'accepted': []}
    if kind == 'short':
        row['given'] = answer if isinstance(answer, str) else ''
        row['accepted'] = question.get('accepted', [])
        return row
    right = set(question.get('correct_set', [])) if kind == 'multiple' else {question['correct']}
    chosen = set(answer) if isinstance(answer, list) else {answer} if answer is not None else set()
    row['options'] = [
        {'text': text, 'correct': i in right, 'chosen': i in chosen} for i, text in enumerate(question['options'])
    ]
    return row


@login_required
def results(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, user=request.user, finished=True)
    rows = [review_row(q, attempt.answers.get(str(q['id']))) for q in attempt.frozen_questions()]
    assessment = attempt.assessment
    topics = {}
    for row in rows:
        topic = row['question'].get('topic') or ''
        if topic:
            bucket = topics.setdefault(topic, {'topic': topic, 'total': 0, 'ok': 0})
            bucket['total'] += 1
            bucket['ok'] += row['status'] == 'ok'
    topic_rows = sorted(
        ({**b, 'pct': round(100 * b['ok'] / b['total'])} for b in topics.values()), key=lambda b: (b['pct'], b['topic'])
    )
    finished = Attempt.objects.filter(user=request.user, assessment=assessment, finished=True)
    return render(
        request,
        'result.html',
        ctx(
            request,
            'results',
            attempt=attempt,
            rows=rows,
            ok_count=sum(r['status'] == 'ok' for r in rows),
            wrong_count=sum(r['status'] == 'wrong' for r in rows),
            blank_count=sum(r['status'] == 'blank' for r in rows),
            passed=attempt.score >= assessment.pass_score,
            topic_rows=topic_rows,
            certificate=getattr(attempt, 'certificate', None),
            history=finished.order_by('-started')[:8],
            can_retry=not assessment.max_attempts or finished.count() < assessment.max_attempts,
        ),
    )
