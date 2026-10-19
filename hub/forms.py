from django import forms
from django.contrib.auth.models import User

from .models import TRUE_FALSE_OPTIONS, Question, ResourceVersion

MIN_OPTIONS, MAX_OPTIONS = 2, 6


def lines_of(text):
    return [line.strip() for line in (text or '').splitlines() if line.strip()]


class QuestionForm(forms.ModelForm):
    """Editor de preguntas. Según el tipo se usan las opciones (una por línea), los números correctos o las respuestas aceptadas."""

    options_text = forms.CharField(
        required=False,
        label='Opciones (una por línea)',
        widget=forms.Textarea(attrs={'rows': 6, 'data-for': 'single multiple'}),
        help_text=f'Entre {MIN_OPTIONS} y {MAX_OPTIONS} opciones. Cada línea es una opción.',
    )
    correct_number = forms.IntegerField(
        required=False,
        label='Número de la opción correcta',
        min_value=1,
        max_value=MAX_OPTIONS,
        widget=forms.NumberInput(attrs={'data-for': 'single truefalse'}),
        help_text='1 es la primera línea. En verdadero/falso: 1 = Verdadero, 2 = Falso.',
    )
    correct_numbers_text = forms.CharField(
        required=False,
        label='Números de las opciones correctas',
        widget=forms.TextInput(attrs={'data-for': 'multiple', 'placeholder': 'Por ejemplo: 1, 3'}),
        help_text='Separados por comas. Hay que marcar exactamente esas opciones.',
    )
    accepted_text = forms.CharField(
        required=False,
        label='Respuestas aceptadas (una por línea)',
        widget=forms.Textarea(attrs={'rows': 3, 'data-for': 'short'}),
        help_text='Se ignoran mayúsculas, acentos y espacios repetidos al comparar.',
    )

    class Meta:
        model = Question
        fields = ['assessment', 'kind', 'topic', 'text', 'explanation']
        labels = {
            'assessment': 'Evaluación',
            'kind': 'Tipo de pregunta',
            'topic': 'Tema (opcional)',
            'text': 'Enunciado',
            'explanation': 'Explicación de la respuesta',
        }
        widgets = {'text': forms.Textarea(attrs={'rows': 3}), 'explanation': forms.Textarea(attrs={'rows': 3})}

    field_order = [
        'assessment',
        'kind',
        'topic',
        'text',
        'options_text',
        'correct_number',
        'correct_numbers_text',
        'accepted_text',
        'explanation',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        question = self.instance
        if question.pk:
            self.fields['options_text'].initial = '\n'.join(question.options)
            self.fields['correct_number'].initial = question.correct + 1
            self.fields['correct_numbers_text'].initial = ', '.join(str(i + 1) for i in question.correct_set)
            self.fields['accepted_text'].initial = '\n'.join(question.accepted)

    def _parse_numbers(self, text, size):
        try:
            numbers = [int(part) for part in (text or '').replace(';', ',').split(',') if part.strip()]
        except ValueError:
            numbers = None
        if not numbers or len(set(numbers)) != len(numbers) or any(n < 1 or n > size for n in numbers):
            self.add_error('correct_numbers_text', f'Escribe uno o más números entre 1 y {size}, sin repetir.')
            return None
        return numbers

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get('kind')
        if not kind:
            return cleaned
        options, correct, correct_set, accepted = [], 0, [], []
        if kind == 'short':
            accepted = lines_of(cleaned.get('accepted_text'))
            if not accepted:
                self.add_error('accepted_text', 'Escribe al menos una respuesta aceptada.')
        elif kind == 'truefalse':
            options = list(TRUE_FALSE_OPTIONS)
            correct = (cleaned.get('correct_number') or 0) - 1
            if correct not in (0, 1):
                self.add_error('correct_number', 'Elige 1 (Verdadero) o 2 (Falso).')
        else:
            options = lines_of(cleaned.get('options_text'))
            if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
                self.add_error('options_text', f'Escribe entre {MIN_OPTIONS} y {MAX_OPTIONS} opciones, una por línea.')
            elif len(set(options)) != len(options):
                self.add_error('options_text', 'Hay opciones repetidas.')
            elif kind == 'multiple':
                numbers = self._parse_numbers(cleaned.get('correct_numbers_text'), len(options))
                correct_set = [n - 1 for n in numbers] if numbers else []
            else:
                number = cleaned.get('correct_number')
                if not number or number > len(options):
                    self.add_error('correct_number', f'Elige un número entre 1 y {len(options)}.')
                else:
                    correct = number - 1
        if not self.errors:
            # Se asignan aquí para que Question.clean (que valida la instancia) vea los valores finales.
            self.instance.options = options
            self.instance.correct = correct
            self.instance.correct_set = correct_set
            self.instance.accepted = accepted
        return cleaned

    def _post_clean(self):
        # Si ya hay errores propios no se valida el modelo: Question.clean informaría de campos que no están en el formulario.
        if not self.errors:
            super()._post_clean()


class ResourceVersionForm(forms.ModelForm):
    """Subida de una versión nueva de un recurso (documento o video) sin pasar por Django Admin."""

    class Meta:
        model = ResourceVersion
        fields = ['file', 'notes']
        labels = {'file': 'Archivo', 'notes': 'Notas de la versión'}
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Selecciona un archivo.')
        return file


class ProfileForm(forms.ModelForm):
    """Datos que la propia persona puede actualizar. El correo es el que usan la recuperación de contraseña y los avisos."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Nombre', 'last_name': 'Apellido', 'email': 'Correo electrónico'}
