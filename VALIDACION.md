# Validación CICC

15 de octubre de 2026. Windows, Python 3.12, Django 5.2.18 y openpyxl 3.1.5; SQLite en memoria.

- manage.py check: sin incidencias.
- manage.py makemigrations --check --dry-run: sin cambios pendientes.
- manage.py test hub: 12 pruebas aprobadas, 6,272 segundos.

Se conservaron y ejecutaron las ocho pruebas originales: roles, pantallas, autoguardado, calificación, aislamiento de usuarios, expiración, progreso, archivos protegidos, búsqueda, validación de respuestas, Excel y rollback. Cuatro pruebas nuevas verifican módulos y marca, mapa, búsqueda en descripciones y academia, exclusión de recursos no publicados y respuestas del banco, carga repetible y área Transversal.

Pendiente: revisión visual en navegador, pruebas PostgreSQL e instalación en un Windows limpio. La videoteca contiene fichas de referencia sin grabaciones adjuntas. El mapa es ilustrativo y no representa infraestructura real. El módulo de certificación no se conecta a sistemas externos ni emite certificados.