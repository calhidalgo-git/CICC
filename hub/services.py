"""Reglas de negocio compartidas por las vistas y los comandos de gestión."""

import random
import re
import unicodedata
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Assessment, Attempt, Audit, Certificate, Notification

MAX_SHORT_ANSWER = 200
CLOSING_WINDOW = timedelta(hours=48)


def log(user, action):
    Audit.objects.create(user=user, action=action)


def issue_certificate(attempt):
    """Emite la constancia si el intento aprobó. Es idempotente."""
    questions = attempt.frozen_questions()
    if questions and attempt.score >= attempt.assessment.pass_score:
        certificate, _ = Certificate.objects.get_or_create(attempt=attempt)
        return certificate
    return None


def send_result_email(attempt):
    """Avisa el resultado por correo si la persona tiene uno registrado. Nunca interrumpe el flujo."""
    user = attempt.user
    if not user.email:
        return False
    assessment = attempt.assessment
    passed = attempt.score >= assessment.pass_score
    lines = [
        f'Hola {user.get_full_name() or user.username},',
        '',
        f'Terminaste «{assessment.title}» con {attempt.score}% (aprobación: {assessment.pass_score}%).',
        'Aprobaste. ¡Felicitaciones!'
        if passed
        else 'Esta vez no alcanzaste el umbral; revisa la retroalimentación y vuelve a intentarlo.',
        f'Resultado: {settings.SITE_URL}/results/{attempt.pk}/',
    ]
    certificate = getattr(attempt, 'certificate', None)
    if certificate:
        lines.append(f'Certificado: {settings.SITE_URL}/certificate/{certificate.code}/')
    send_mail(f'Resultado de «{assessment.title}»', '\n'.join(lines), None, [user.email], fail_silently=True)
    return True


def normalize(text):
    """Minúsculas, sin acentos ni espacios repetidos: «  Código  » y «codigo» cuentan como lo mismo."""
    decomposed = unicodedata.normalize('NFKD', str(text))
    stripped = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r'\s+', ' ', stripped).strip().casefold()


def is_correct(question, answer):
    """Compara la respuesta con la pregunta según su tipo. Las copias antiguas sin tipo son de selección única."""
    kind = question.get('kind', 'single')
    if answer is None:
        return False
    if kind == 'multiple':
        return isinstance(answer, list) and sorted(set(answer)) == sorted(question.get('correct_set', []))
    if kind == 'short':
        return isinstance(answer, str) and normalize(answer) in {normalize(a) for a in question.get('accepted', [])}
    return answer == question['correct']


def is_blank(answer):
    return answer is None or answer == '' or answer == []


def valid_answer(question, value):
    """Valida la forma de una respuesta recibida del navegador."""
    kind = question.get('kind', 'single')
    size = len(question.get('options', []))
    if kind == 'short':
        return isinstance(value, str) and len(value) <= MAX_SHORT_ANSWER
    if kind == 'multiple':
        return (
            isinstance(value, list)
            and len(value) <= size
            and len(set(value)) == len(value)
            and all(type(v) is int and 0 <= v < size for v in value)
        )
    return type(value) is int and 0 <= value < size


def draw_questions(questions, count):
    """Elige `count` preguntas repartidas entre los temas (por turnos) y las mezcla. 0 o más que el banco = todas."""
    pool = list(questions)
    random.shuffle(pool)
    if not count or count >= len(pool):
        return pool
    buckets = {}
    for question in pool:
        buckets.setdefault(question.topic, []).append(question)
    chosen = []
    queues = list(buckets.values())
    while len(chosen) < count:
        for queue in queues:
            if queue and len(chosen) < count:
                chosen.append(queue.pop())
    random.shuffle(chosen)
    return chosen


def _audience(assessment):
    """Personas activas con correo a quienes aplica la evaluación (sus grupos, o todas si no tiene)."""
    people = User.objects.filter(is_active=True).exclude(email='')
    groups = assessment.groups.all()
    return people.filter(groups__in=groups).distinct() if groups else people


def send_assessment_notices(now=None):
    """Avisa una sola vez de evaluaciones asignadas ya abiertas y de plazos que vencen pronto. Devuelve (asignadas, plazos)."""
    now = now or timezone.now()
    assigned = closing = 0
    for assessment in Assessment.objects.prefetch_related('groups'):
        if assessment.availability(now) or not assessment.questions.exists():
            continue
        link = f'{settings.SITE_URL}/p/assessments/'
        for user in _audience(assessment):
            name = user.get_full_name() or user.username
            if (
                assessment.groups.exists()
                and not Notification.objects.filter(user=user, assessment=assessment, kind='assigned').exists()
            ):
                body = f'Hola {name},\n\nTienes asignada la evaluación «{assessment.title}» ({assessment.minutes} minutos).\n{link}'
                send_mail(f'Evaluación asignada: {assessment.title}', body, None, [user.email], fail_silently=True)
                Notification.objects.get_or_create(user=user, assessment=assessment, kind='assigned')
                assigned += 1
            if assessment.closes_at and assessment.closes_at - now <= CLOSING_WINDOW:
                done = Attempt.objects.filter(user=user, assessment=assessment, finished=True).exists()
                if (
                    not done
                    and not Notification.objects.filter(user=user, assessment=assessment, kind='closing').exists()
                ):
                    when = timezone.localtime(assessment.closes_at)
                    body = f'Hola {name},\n\nLa evaluación «{assessment.title}» cierra el {when:%d/%m/%Y a las %H:%M}.\n{link}'
                    send_mail(f'Cierra pronto: {assessment.title}', body, None, [user.email], fail_silently=True)
                    Notification.objects.get_or_create(user=user, assessment=assessment, kind='closing')
                    closing += 1
    return assigned, closing


def grade(attempt):
    """Califica con las preguntas congeladas del intento, lo cierra y emite certificado y aviso."""
    questions = attempt.frozen_questions()
    correct = sum(is_correct(q, attempt.answers.get(str(q['id']))) for q in questions)
    attempt.score = round(100 * correct / len(questions), 1) if questions else 0
    attempt.finished = True
    attempt.finished_at = min(timezone.now(), attempt.deadline)
    attempt.save()
    issue_certificate(attempt)
    transaction.on_commit(
        lambda: send_result_email(Attempt.objects.select_related('user', 'assessment').get(pk=attempt.pk))
    )


def close_if_expired(attempt):
    if not attempt.finished and timezone.now() >= attempt.deadline:
        grade(attempt)
        log(attempt.user, f'Evaluación {attempt.pk} cerrada por tiempo: {attempt.score}%')
    return attempt
