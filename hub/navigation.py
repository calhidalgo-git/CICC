"""Estructura del menú lateral y permisos de cada sección."""

from .catalog import MODULES

MODULE_ICONS = {
    'knowledge': 'lightbulb',
    'environment': 'server',
    'mainframe': 'cpu',
    'distributed': 'network',
    'lifecycle': 'refresh',
    'tools': 'wrench',
    'procedures': 'checklist',
    'incidents': 'alert',
    'glossary': 'glossary',
}

# (clave, etiqueta, [(slug, etiqueta, icono)])
NAV_GROUPS = [
    (
        'learn',
        'Aprender',
        [
            ('dashboard', 'Vista general', 'dashboard'),
            ('library', 'Biblioteca', 'library'),
            ('videos', 'Videoteca', 'video'),
            ('links', 'Enlaces útiles', 'link'),
            ('favorites', 'Mis favoritos', 'star'),
            ('paths', 'Rutas de aprendizaje', 'path'),
            ('lessons', 'Mis lecciones', 'lesson'),
            ('search', 'Búsqueda global', 'search'),
        ],
    ),
    (
        'knowledge',
        'Conocimiento QA',
        [(slug, label, MODULE_ICONS[slug]) for slug, label in MODULES.items()]
        + [('components', 'Mapa de componentes', 'components')],
    ),
    (
        'assess',
        'Evaluación',
        [
            ('assessments', 'Evaluaciones', 'assessment'),
            ('results', 'Mis resultados', 'results'),
            ('certificates', 'Mis certificados', 'award'),
        ],
    ),
    (
        'manage',
        'Gestión y control',
        [
            ('questions', 'Banco de preguntas', 'questions'),
            ('reports', 'Reportes', 'reports'),
            ('users', 'Usuarios', 'users'),
            ('roles', 'Roles y permisos', 'roles'),
            ('settings', 'Configuración', 'settings'),
            ('audit', 'Auditoría', 'audit'),
            ('backups', 'Respaldos', 'backup'),
        ],
    ),
]

NAV = [item for _, _, items in NAV_GROUPS for item in items]
TITLES = {slug: label for slug, label, _ in NAV}
SLUGS = set(TITLES)

GATES = {
    'questions': 'hub.change_question',
    'reports': 'hub.view_audit',
    'users': 'auth.view_user',
    'roles': 'auth.view_group',
    'settings': 'auth.change_group',
    'audit': 'hub.view_audit',
    'backups': 'hub.view_audit',
}


def allowed(user, slug):
    return slug not in GATES or user.has_perm(GATES[slug])


def groups_for(user, section):
    """Grupos del menú visibles para el usuario; marca el grupo de la sección activa."""
    groups = []
    for key, label, items in NAV_GROUPS:
        visible = [item for item in items if allowed(user, item[0])]
        if visible:
            groups.append(
                {'key': key, 'label': label, 'items': visible, 'active': any(slug == section for slug, _, _ in visible)}
            )
    return groups
