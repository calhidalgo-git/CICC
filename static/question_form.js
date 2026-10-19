// Editor de preguntas: muestra solo los campos del tipo elegido y una vista previa en vivo.
(() => {
    const form = document.getElementById('question-form');
    if (!form) return;
    const field = (name) => form.querySelector(`[name=${name}]`);
    const kind = field('kind');
    const text = field('text');
    const options = field('options_text');
    const correct = field('correct_number');
    const correctSet = field('correct_numbers_text');
    const accepted = field('accepted_text');
    const previewText = document.getElementById('preview-text');
    const previewOptions = document.getElementById('preview-options');

    const lines = (value) => value.split('\n').map((l) => l.trim()).filter(Boolean);

    function toggleFields() {
        form.querySelectorAll('.field[data-for]').forEach((wrapper) => {
            const allowed = wrapper.dataset.for.split(' ').filter(Boolean);
            wrapper.hidden = allowed.length > 0 && !allowed.includes(kind.value);
        });
    }

    function row(label, isCorrect, prefix) {
        const div = document.createElement('div');
        div.className = 'option' + (isCorrect ? ' is-correct' : '');
        div.textContent = (isCorrect ? '✓ ' : '') + (prefix || '') + label;
        return div;
    }

    function render() {
        previewText.textContent = text.value.trim() || '—';
        let items = [];
        if (kind.value === 'short') {
            const answers = lines(accepted.value);
            items = [row('[ campo de texto ]', false), ...answers.map((a) => row(a, true, 'Acepta: '))];
        } else if (kind.value === 'truefalse') {
            const right = Number(correct.value);
            items = ['Verdadero', 'Falso'].map((label, i) => row(label, right === i + 1));
        } else if (kind.value === 'multiple') {
            const right = new Set(correctSet.value.split(/[,;]/).map((n) => Number(n.trim())));
            items = lines(options.value).map((label, i) => row(label, right.has(i + 1), '☐ '));
        } else {
            const right = Number(correct.value);
            items = lines(options.value).map((label, i) => row(label, i + 1 === right));
        }
        previewOptions.replaceChildren(...items);
    }

    kind.addEventListener('change', () => {
        toggleFields();
        render();
    });
    [text, options, correct, correctSet, accepted].forEach((el) => el.addEventListener('input', render));
    toggleFields();
    render();
})();
