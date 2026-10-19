// Evaluación en curso: autoguardado, mapa de preguntas, marcas de revisión, avisos de tiempo y confirmación de envío.
// Admite selección única y verdadero/falso (radio), selección múltiple (casillas) y respuesta corta (texto).
(() => {
    const root = document.getElementById('exam-root');
    if (!root) return;

    const attemptId = root.dataset.attempt;
    const total = Number(root.dataset.total);
    const saveUrl = root.dataset.saveUrl;
    const resultsUrl = root.dataset.resultsUrl;
    // El reloj se alinea con el servidor para no depender de la hora del equipo del participante.
    const skew = new Date(root.dataset.serverNow).getTime() - Date.now();
    const deadline = new Date(root.dataset.deadline).getTime();

    const form = document.getElementById('answers');
    const finishForm = document.getElementById('finish');
    const statusEl = document.getElementById('save-status');
    const timerEl = document.getElementById('timer');
    const alertEl = document.getElementById('time-alert');
    const meter = document.getElementById('meter');
    const counter = document.getElementById('answered-count');
    const dialog = document.getElementById('finish-dialog');
    const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const flagKey = 'cicc:flags:' + attemptId;

    let dirty = false;
    let expired = false;
    let chain = Promise.resolve();
    let typingTimer = null;

    const nowMs = () => Date.now() + skew;
    const fieldsets = [...form.querySelectorAll('fieldset.question')];
    const questionIds = fieldsets.map((f) => f.dataset.id);
    const fieldsetOf = (id) => fieldsets.find((f) => f.dataset.id === id);

    // Respuesta actual de una pregunta según su tipo; null si está sin responder.
    function answerOf(fieldset) {
        const kind = fieldset.dataset.kind;
        if (kind === 'short') {
            const text = fieldset.querySelector('input[type=text]').value.trim();
            return text || null;
        }
        if (kind === 'multiple') {
            const picked = [...fieldset.querySelectorAll('input[type=checkbox]:checked')].map((i) => Number(i.value));
            return picked.length ? picked : null;
        }
        const checked = fieldset.querySelector('input[type=radio]:checked');
        return checked ? Number(checked.value) : null;
    }

    function setAnswer(fieldset, value) {
        const kind = fieldset.dataset.kind;
        if (kind === 'short') {
            fieldset.querySelector('input[type=text]').value = typeof value === 'string' ? value : '';
        } else if (kind === 'multiple') {
            const picked = new Set(Array.isArray(value) ? value : []);
            fieldset.querySelectorAll('input[type=checkbox]').forEach((i) => (i.checked = picked.has(Number(i.value))));
        } else {
            const input = fieldset.querySelector(`input[type=radio][value="${value}"]`);
            if (input) input.checked = true;
        }
    }

    // Marcas de revisión (solo en este navegador)
    let flags = new Set();
    try {
        flags = new Set(JSON.parse(sessionStorage.getItem(flagKey) || '[]'));
    } catch (_) {}
    const persistFlags = () => {
        try {
            sessionStorage.setItem(flagKey, JSON.stringify([...flags]));
        } catch (_) {}
    };

    const answered = () => questionIds.filter((id) => answerOf(fieldsetOf(id)) !== null);

    function refresh() {
        const done = answered();
        counter.textContent = `${done.length} de ${total}`;
        meter.style.width = `${(100 * done.length) / total}%`;
        meter.parentElement.setAttribute('aria-valuenow', String(done.length));
        questionIds.forEach((id) => {
            const btn = document.querySelector(`.map-btn[data-id="${id}"]`);
            btn.classList.toggle('answered', done.includes(id));
            btn.classList.toggle('flagged', flags.has(id));
            fieldsetOf(id).querySelector('.flag-btn').setAttribute('aria-pressed', String(flags.has(id)));
        });
    }

    // Respuestas guardadas
    const saved = JSON.parse(document.getElementById('saved-answers').textContent);
    for (const [key, value] of Object.entries(saved)) {
        const fieldset = fieldsetOf(key);
        if (fieldset) setAnswer(fieldset, value);
    }
    statusEl.textContent = Object.keys(saved).length ? '✓ Respuestas recuperadas · Autoguardado activado' : 'Autoguardado activado';
    refresh();

    function snapshot() {
        const data = {};
        fieldsets.forEach((fieldset) => {
            const value = answerOf(fieldset);
            if (value !== null) data[fieldset.dataset.id] = value;
        });
        return data;
    }

    function save() {
        const body = JSON.stringify(snapshot());
        chain = chain
            .catch(() => {})
            .then(async () => {
                statusEl.textContent = 'Guardando…';
                const response = await fetch(saveUrl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
                    body,
                });
                if (!response.ok) {
                    const payload = await response.json().catch(() => ({}));
                    if (payload.expired) {
                        expired = true;
                        location.href = resultsUrl;
                        return;
                    }
                    throw new Error('No guardado');
                }
                dirty = false;
                statusEl.textContent = '✓ Guardado en el servidor · ' + new Date().toLocaleTimeString('es-PE');
            });
        return chain;
    }

    const saveQuietly = () =>
        save().catch(() => {
            statusEl.textContent = 'Sin conexión. Mantén esta página abierta; reintentaremos automáticamente.';
        });

    // Las opciones guardan al instante; el texto espera a que dejes de escribir.
    form.addEventListener('input', (event) => {
        dirty = true;
        refresh();
        clearTimeout(typingTimer);
        if (event.target.type === 'text') {
            typingTimer = setTimeout(saveQuietly, 700);
        } else {
            saveQuietly();
        }
    });
    // Solo reintenta cuando hay cambios sin confirmar; no escribe en vano.
    setInterval(() => {
        if (dirty && !expired) saveQuietly();
    }, 10000);

    window.addEventListener('beforeunload', (event) => {
        if (dirty && !expired) {
            event.preventDefault();
            event.returnValue = '';
        }
    });

    form.querySelectorAll('.flag-btn').forEach((btn) =>
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            flags.has(id) ? flags.delete(id) : flags.add(id);
            persistFlags();
            refresh();
        }),
    );

    // Confirmación de envío con resumen
    function summary() {
        const done = answered();
        const missing = questionIds.map((id, i) => [id, i + 1]).filter(([id]) => !done.includes(id));
        const flagged = questionIds.filter((id) => flags.has(id)).length;
        const parts = [`Contestaste ${done.length} de ${total} preguntas.`];
        if (missing.length) parts.push(`Sin responder: ${missing.map(([, n]) => n).join(', ')}.`);
        if (flagged) parts.push(`Marcadas para revisar: ${flagged}.`);
        document.getElementById('dialog-summary').textContent = parts.join(' ');
    }

    async function submitNow() {
        const button = document.getElementById('confirm-finish');
        button.disabled = true;
        try {
            await save();
            if (!expired) finishForm.submit();
        } catch (_) {
            button.disabled = false;
            statusEl.textContent = 'No se envió: no pudimos guardar tus respuestas. Revisa tu conexión e inténtalo de nuevo.';
            if (dialog.open) dialog.close();
        }
    }

    document.getElementById('finish-button').addEventListener('click', () => {
        summary();
        if (typeof dialog.showModal === 'function') dialog.showModal();
        else if (confirm(document.getElementById('dialog-summary').textContent + ' ¿Enviar la evaluación?')) submitNow();
    });
    document.getElementById('cancel-finish').addEventListener('click', () => dialog.close());
    document.getElementById('confirm-finish').addEventListener('click', submitNow);

    // Reloj y avisos
    const warned = new Set();
    function warn(level, message) {
        if (warned.has(level)) return;
        warned.add(level);
        alertEl.textContent = message;
        alertEl.hidden = false;
        alertEl.classList.toggle('danger', level === 'last');
        document.getElementById('time-live').textContent = message;
    }

    function tick() {
        const seconds = Math.max(0, Math.ceil((deadline - nowMs()) / 1000));
        timerEl.textContent = String(Math.floor(seconds / 60)).padStart(2, '0') + ':' + String(seconds % 60).padStart(2, '0');
        timerEl.classList.toggle('warn', seconds <= 300 && seconds > 60);
        timerEl.classList.toggle('danger', seconds <= 60);
        if (seconds <= 300 && seconds > 60) warn('five', 'Quedan 5 minutos. Revisa las preguntas sin responder.');
        if (seconds <= 60 && seconds > 0) warn('last', 'Queda menos de 1 minuto. Tus respuestas se enviarán automáticamente al terminar el tiempo.');
        if (!seconds && !expired) {
            expired = true;
            alertEl.hidden = false;
            alertEl.classList.add('danger');
            alertEl.textContent = 'Se acabó el tiempo. Enviando tu evaluación…';
            if (dialog.open) dialog.close();
            setTimeout(() => finishForm.submit(), 1200);
        }
    }
    tick();
    setInterval(tick, 1000);
})();
