"""Editor propio del banco de preguntas (alternativa a Django Admin)."""

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import QuestionForm
from ..models import Question
from .common import ctx, log


def question_form(request, question=None):
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        log(request.user, f'{"Edita" if question else "Crea"} pregunta {saved.pk}')
        messages.success(request, 'Pregunta guardada. Los intentos ya iniciados conservan su propia copia.')
        return redirect('/p/questions/')
    return render(
        request,
        'question_form.html',
        ctx(
            request,
            'questions',
            form=form,
            question=question,
            title='Editar pregunta' if question else 'Nueva pregunta',
        ),
    )


@permission_required('hub.add_question', raise_exception=True)
def question_new(request):
    return question_form(request)


@permission_required('hub.change_question', raise_exception=True)
def question_edit(request, pk):
    return question_form(request, get_object_or_404(Question, pk=pk))


@permission_required('hub.delete_question', raise_exception=True)
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    log(request.user, f'Elimina pregunta {question.pk}')
    question.delete()
    messages.success(request, 'Pregunta eliminada. Los intentos ya iniciados conservan su copia.')
    return redirect('/p/questions/')
