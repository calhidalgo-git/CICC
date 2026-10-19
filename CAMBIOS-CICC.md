# Ampliación sobre el proyecto original

Fuente: ZIP adjunto QA-Knowledge-Hub.zip, SHA256 BF78E4F297509E2AB5C12D7C14B46BC3B02C5AF9B128B99EAE536090C7894EA3.

Se conservaron config, hub, modelos originales, migraciones, plantillas, CSS, recursos locales Bootstrap/Chart.js, evaluaciones, autoguardado, permisos, importación y exportación Excel. No se reconstruyó la aplicación.

Se añadió catalog.py con 26 recursos ficticios: diez guías y escenarios y dieciséis entradas de glosario. Se amplió la academia con diez lecciones, manteniendo las seis originales. Hay 32 recursos, tres rutas, dieciséis lecciones, dos evaluaciones y seis preguntas al iniciar una base limpia.

La navegación incorpora conocimiento del área, ambiente de certificación, Mainframe, Distribuido, ciclo de vida y pruebas, herramientas QA/ClearQuest, procedimientos, incidentes, glosario, mapa conceptual y búsqueda global. El mapa enlaza con los módulos relacionados. Se mantienen las cinco familias visuales: ejecutivo, biblioteca, academia, evaluaciones y analítica; los módulos nuevos usan biblioteca.

La búsqueda global encuentra títulos, descripciones y áreas de recursos publicados, títulos y cuerpos de lecciones, rutas y títulos/áreas de evaluaciones. No busca respuestas de examen, usuarios ni auditoría. La biblioteca mantiene filtros locales. Todos los módulos requieren autenticación; la administración sigue sujeta a permisos Django.

La migración 0003 permite el área Transversal. Los módulos usan Resource existente y se editan en Django Admin; se identifica cada categoría con el campo kind (knowledge, environment, mainframe, distributed, lifecycle, tools, procedures, incidents o glossary). Las claves internas originales QA_SQLITE y config/hub se conservan para compatibilidad con instalaciones previas.

Sobre una instalación existente: respalda primero la base y private_storage, sustituye código, instala requisitos y ejecuta migrate. seed_demo agrega ejemplos y actualiza los 26 recursos CICC por título; ejecútalo solo si deseas esos ejemplos. No borra recursos originales. Revisa roles porque seed_demo vuelve a asignar los permisos de los grupos demo.

## Mejoras de calidad, diseño y funcionalidad (19 de octubre de 2026)

**Seguridad.** Con `DEBUG=0` ahora se exige `DJANGO_SECRET_KEY` y se activan cookies Secure, HTTPS y HSTS; en Vercel `DEBUG` es `0` por defecto. Límite de 5 intentos fallidos de acceso por 15 minutos. Las credenciales demo solo se muestran con `DEBUG=1` o `SHOW_DEMO_CREDENTIALS=1`. WhiteNoise sirve los estáticos. Validadores de contraseña y cabeceras `nosniff` y `Referrer-Policy`. Las exportaciones Excel neutralizan fórmulas.

**Datos.** Migración 0004: intento abierto único por usuario y evaluación, copia de las preguntas dentro de cada intento, fecha de cierre, límite de intentos, opciones válidas para área y tipo, campo `landing` en recursos (sustituye la detección por título) y favoritos. La migración cierra intentos abiertos duplicados y asigna `landing` a los recursos existentes. `demo.sqlite3` ya está migrada. Los intentos vencidos se califican al abrirlos. El respaldo incluye grupos y usuarios (sin contraseñas) y es restaurable con `loaddata`.

**Código.** `hub/views.py` se dividió en `hub/views/` (páginas, aprendizaje, evaluaciones, herramientas); cada sección calcula solo sus datos y las listas se paginan. `page.html` se separó en `templates/sections/`. El catálogo pasó a `hub/content/catalog.json`. Menú y permisos en `hub/navigation.py`. Código formateado con ruff; pruebas unificadas (49); CI en GitHub Actions.

**Diseño.** Tipografía mínima de 11 px y contraste AA en textos secundarios; fuente de sistema en lugar de solo Segoe UI; iconos SVG locales; menú agrupado y plegable; enlace «Saltar al contenido», foco visible y `prefers-reduced-motion`; estados vacíos; datos antes fijos (insignia de evaluaciones, número de lecciones, áreas, rol) ahora vienen de la base. Chart.js solo se carga en Reportes.

**Funcionalidad.** Panel con «continúa donde lo dejaste», evaluación en curso y vistos recientemente. Biblioteca con filtros por área y tipo, orden, paginación y favoritos. Búsqueda con resaltado y contadores. Progreso por ruta y paso a la siguiente lección. Examen con mapa de preguntas, marcas de revisión, avisos de tiempo, resumen antes de enviar, preguntas en orden aleatorio y accesibilidad (`fieldset`/`legend`, temporizador con rol). Resultados con tiempo empleado, intentos previos, reintento y revisión de opciones. Reportes con filtros, resumen y exportación filtrada. Cursos semanales con navegación anterior/siguiente. Importación Excel con listado de errores por fila.

## Segunda ronda de mejoras (19 de octubre de 2026)

**Credenciales.** `seed_demo` ya no crea contraseñas conocidas: genera una aleatoria por cuenta nueva y las guarda en `demo-credentials.txt` (excluido de git). Opciones `--password`, `DEMO_PASSWORD` y `--reset-passwords`. La base `demo.sqlite3` incluida se migró y sus cuatro cuentas recibieron contraseñas nuevas, por lo que `DemoQA!2026` dejó de ser válida. La pantalla de acceso ya no imprime contraseñas.

**Evaluaciones.** Editor propio de preguntas (crear, editar, eliminar, vista previa en vivo, de 2 a 6 opciones). Campo de tema y desglose por tema en los resultados, con enlace para reforzar; columna opcional `tema` en la importación Excel. Cohortes: grupos asignados y ventana de apertura y cierre. Certificados con código verificable y página imprimible. Comando `close_expired` para cerrar intentos vencidos. Correo de resultado al terminar.

**Cuentas.** Recuperación de contraseña por correo, cambio de contraseña dentro de la aplicación, validadores de contraseña activos y auditoría del cambio. Correo configurable por variables de entorno.

**Contenido.** Reproductor de video local con soporte de rangos y validación de adjuntos (tipo y tamaño). Semanas de los cursos editables desde el administrador (`export_weeks` las copia a la base) y marcado de semanas completadas con progreso en las portadas y el panel.

**Diseño.** Modo oscuro con botón en el encabezado y respeto a la preferencia del sistema.

**Operación.** `START-DEMO.ps1` reescrito: comprueba Python 3.12+, reinstala dependencias solo si cambian, detecta puerto ocupado, abre el navegador y ofrece `-Port`, `-NoBrowser` y `-Reset`. CI con un trabajo adicional contra PostgreSQL. Las pruebas usan una carpeta temporal para adjuntos y un hasher rápido (82 pruebas).

**No se hizo:** autenticación en dos pasos, CSP, límite de solicitudes de recuperación de contraseña, pruebas de navegador (Playwright), revisión con lector de pantalla, aplanar la carpeta anidada `CICC-main/CICC-main` ni quitar `demo.sqlite3` del proyecto (la demo de Vercel lo necesita), tipos de pregunta distintos de selección única y asignación por usuario individual.

## Tercera ronda de mejoras (19 de octubre de 2026)

**Evaluaciones.** Tipos de pregunta: selección única, selección múltiple, verdadero/falso y respuesta corta (editor, examen, autoguardado, calificación, resultados y reportes). Sorteo del banco por tema con «Preguntas por intento». Evaluación de práctica con los cuatro tipos en los datos demo.

**Aprendizaje.** Comprobaciones al final de la lección: hay que acertarlas todas para completarla, con explicación de lo fallado. Etiquetas y «Ver también» en los recursos (relaciones explícitas o sugeridas por etiqueta), filtro exacto por etiqueta. Subida de versiones de recursos desde la ficha, con validación de tipo y tamaño.

**Cuentas.** Perfil con datos de contacto editables, progreso, mejores puntajes e historial. Avisos por correo de evaluaciones asignadas y de plazos próximos (`notify_assessments`).

**Administración.** Reportes con gráficos de aprobación por evaluación y evolución diaria, y tabla de las preguntas más falladas (calculada con las preguntas que vio cada persona). Auditoría con filtros por texto, usuario y fechas, y exportación a CSV. Restauración web del respaldo para superusuarios. El respaldo ahora incluye comprobaciones de lección, certificados, semanas, avisos y progreso de semanas, con claves naturales.

**Datos.** Migración 0006 (tipos de pregunta, etiquetas, relaciones, comprobaciones de lección, avisos y preguntas por intento). `demo.sqlite3` ya está al día. Pruebas: 124.

**No se hizo:** autenticación en dos pasos, CSP, límite de solicitudes de recuperación de contraseña, pruebas de navegador (Playwright), revisión con lector de pantalla, aplanar la carpeta anidada `CICC-main/CICC-main`, puntaje parcial en selección múltiple, importación Excel de tipos distintos de selección única y editor visual de las comprobaciones de lección fuera del administrador.

