// Menú lateral: grupos plegables y posición de scroll conservada entre páginas.
(() => {
    const nav = document.querySelector('.sidebar nav');
    if (!nav) return;
    const user = nav.dataset.user;
    const scrollKey = 'cicc:menu-scroll:' + user;
    const groupKey = 'cicc:menu-groups:' + user;

    const read = (key, fallback) => {
        try {
            return JSON.parse(sessionStorage.getItem(key) || 'null') ?? fallback;
        } catch (_) {
            // El menú sigue funcionando si el navegador bloquea el almacenamiento.
            return fallback;
        }
    };
    const write = (key, value) => {
        try {
            sessionStorage.setItem(key, JSON.stringify(value));
        } catch (_) {}
    };

    // Grupos: el de la sección activa siempre abierto; «Aprender» abierto por defecto; el resto recuerda lo elegido.
    const stored = read(groupKey, {});
    nav.querySelectorAll('.nav-group').forEach((group) => {
        const id = group.dataset.group;
        const button = group.querySelector('.nav-toggle');
        const active = group.classList.contains('is-active');
        const collapsed = active ? false : id in stored ? stored[id] : id !== 'learn';
        const apply = (value) => {
            group.classList.toggle('collapsed', value);
            button.setAttribute('aria-expanded', String(!value));
        };
        apply(collapsed);
        button.addEventListener('click', () => {
            const next = !group.classList.contains('collapsed');
            apply(next);
            stored[id] = next;
            write(groupKey, stored);
        });
    });

    const restore = () => {
        const saved = read(scrollKey, null);
        if (saved && Number.isFinite(saved.top) && Number.isFinite(saved.left)) {
            nav.scrollTop = saved.top;
            nav.scrollLeft = saved.left;
        }
    };
    const save = () => write(scrollKey, {top: nav.scrollTop, left: nav.scrollLeft});
    restore();
    nav.addEventListener('scroll', save, {passive: true});
    nav.addEventListener('click', save);
    window.addEventListener('pagehide', save);
    // También cubre la restauración desde la caché de adelante/atrás.
    window.addEventListener('pageshow', restore);
})();
