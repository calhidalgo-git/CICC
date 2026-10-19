"""Catálogo de contenido CICC.

Los textos viven en ``content/catalog.json`` para poder editarlos sin tocar código.
Este módulo solo los carga y conserva la forma que usan el resto de la aplicación
(``MODULES`` como diccionario y ``CONTENT`` como tuplas).
"""

import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / 'content' / 'catalog.json').read_text(encoding='utf-8'))

MODULES = _DATA['modules']
CONTENT = [(c['slug'], c['label'], c['area'], c['title'], c['body']) for c in _DATA['content']]
