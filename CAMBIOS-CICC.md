# Ampliación sobre el proyecto original

Fuente: ZIP adjunto QA-Knowledge-Hub.zip, SHA256 BF78E4F297509E2AB5C12D7C14B46BC3B02C5AF9B128B99EAE536090C7894EA3.

Se conservaron config, hub, modelos originales, migraciones, plantillas, CSS, recursos locales Bootstrap/Chart.js, evaluaciones, autoguardado, permisos, importación y exportación Excel. No se reconstruyó la aplicación.

Se añadió catalog.py con 26 recursos ficticios: diez guías y escenarios y dieciséis entradas de glosario. Se amplió la academia con diez lecciones, manteniendo las seis originales. Hay 32 recursos, tres rutas, dieciséis lecciones, dos evaluaciones y seis preguntas al iniciar una base limpia.

La navegación incorpora conocimiento del área, ambiente de certificación, Mainframe, Distribuido, ciclo de vida y pruebas, herramientas QA/ClearQuest, procedimientos, incidentes, glosario, mapa conceptual y búsqueda global. El mapa enlaza con los módulos relacionados. Se mantienen las cinco familias visuales: ejecutivo, biblioteca, academia, evaluaciones y analítica; los módulos nuevos usan biblioteca.

La búsqueda global encuentra títulos, descripciones y áreas de recursos publicados, títulos y cuerpos de lecciones, rutas y títulos/áreas de evaluaciones. No busca respuestas de examen, usuarios ni auditoría. La biblioteca mantiene filtros locales. Todos los módulos requieren autenticación; la administración sigue sujeta a permisos Django.

La migración 0003 permite el área Transversal. Los módulos usan Resource existente y se editan en Django Admin; se identifica cada categoría con el campo kind (knowledge, environment, mainframe, distributed, lifecycle, tools, procedures, incidents o glossary). Las claves internas originales QA_SQLITE y config/hub se conservan para compatibilidad con instalaciones previas.

Sobre una instalación existente: respalda primero la base y private_storage, sustituye código, instala requisitos y ejecuta migrate. seed_demo agrega ejemplos y actualiza los 26 recursos CICC por título; ejecútalo solo si deseas esos ejemplos. No borra recursos originales. Revisa roles porque seed_demo vuelve a asignar los permisos de los grupos demo.
