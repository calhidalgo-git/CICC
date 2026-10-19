// Keep navigation in place across Django page loads, independently of page scroll.
(() => {
    const nav = document.querySelector('.sidebar nav');
    if (!nav) return;
    const key = 'cicc:menu-scroll:' + nav.dataset.user;
    try {
        const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
        if (saved && Number.isFinite(saved.top) && Number.isFinite(saved.left)) {
            nav.scrollTop = saved.top;
            nav.scrollLeft = saved.left;
        }
    } catch (_) {
        // Navigation remains usable when browser storage is unavailable.
    }
    const save = () => {
        try {
            sessionStorage.setItem(key, JSON.stringify({top: nav.scrollTop, left: nav.scrollLeft}));
        } catch (_) {}
    };
    nav.addEventListener('scroll', save, {passive: true});
    nav.addEventListener('click', save);
    window.addEventListener('pagehide', save);
    window.addEventListener('pageshow', () => {
        // Also handles Back/Forward cache restoration without moving the page.
        try {
            const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
            if (saved && Number.isFinite(saved.top) && Number.isFinite(saved.left)) {
                nav.scrollTop = saved.top;
                nav.scrollLeft = saved.left;
            }
        } catch (_) {}
    });
})();
