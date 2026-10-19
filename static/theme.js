// Tema claro/oscuro. Se aplica antes de pintar (script síncrono en <head>) para evitar parpadeos.
(() => {
    const KEY = 'cicc:theme';
    const root = document.documentElement;
    const stored = () => {
        try {
            return localStorage.getItem(KEY);
        } catch (_) {
            return null;
        }
    };
    const preferred = () => stored() || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const apply = (theme) => {
        root.dataset.theme = theme;
        const button = document.getElementById('theme-toggle');
        if (button) {
            const dark = theme === 'dark';
            button.setAttribute('aria-pressed', String(dark));
            button.setAttribute('aria-label', dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
            button.title = button.getAttribute('aria-label');
        }
    };
    apply(preferred());
    document.addEventListener('DOMContentLoaded', () => {
        apply(root.dataset.theme);
        const button = document.getElementById('theme-toggle');
        if (!button) return;
        button.addEventListener('click', () => {
            const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
            try {
                localStorage.setItem(KEY, next);
            } catch (_) {}
            apply(next);
        });
    });
})();
