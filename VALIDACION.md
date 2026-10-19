# Validación CICC

19 de octubre de 2026. Windows, Python 3.14, Django 5.2.x y openpyxl 3.1.5; SQLite en memoria.

- manage.py check: sin incidencias.
- manage.py makemigrations --check --dry-run: sin cambios pendientes.
- manage.py test hub: 124 pruebas aprobadas (las 12 originales y 112 nuevas).
- ruff format --check y ruff check: sin hallazgos.
- manage.py check --deploy con DEBUG=0: solo avisos conscientes (HSTS con subdominios y precarga desactivados).
- Revisión en navegador adicional: examen con los cuatro tipos de pregunta (autoguardado, restauración al recargar, envío, nota y desglose por tema) sin errores de consola.
- Revisión en navegador (Chrome, servidor local): panel, biblioteca (18 tarjetas, filtros y paginación) y examen completo (autoguardado, mapa de avance, diálogo de envío y página de resultados) sin errores de consola.

Pendiente: revisión visual detallada con capturas (la herramienta de capturas del navegador se bloqueó; la verificación fue por DOM y consola), pruebas con PostgreSQL, revisión en móvil real e instalación en un Windows limpio. La videoteca contiene fichas de referencia sin grabaciones adjuntas. El mapa es ilustrativo y no representa infraestructura real. El módulo de certificación no se conecta a sistemas externos ni emite certificados.