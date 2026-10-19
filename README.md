# CICC — Centro Integral de Conocimiento de Calidad

Prototipo Django navegable en español para personal QA Mainframe y Distribuido, con 32 recursos, 16 lecciones y búsqueda global de recursos, academia, rutas y evaluaciones. Incluye conocimiento del área, ambiente de certificación, mapa conceptual, Mainframe, Distribuido, ciclo de vida y pruebas, QA/ClearQuest, procedimientos, incidentes y glosario. Todos los escenarios y accesos son ficticios.

Todas las herramientas son gratuitas y de código abierto. No requiere servicios de pago ni conexión para su interfaz: Bootstrap, Chart.js y los iconos se incluyen localmente. El ambiente de certificación es formativo y ClearQuest se describe sin integración.

**Windows, demo sin PostgreSQL:** extrae el ZIP y ejecuta `powershell -ExecutionPolicy Bypass -File .\START-DEMO.ps1` desde la carpeta del proyecto. Consulta [INSTRUCCIONES-WINDOWS.md](INSTRUCCIONES-WINDOWS.md). Las contraseñas de la demo se generan al prepararla y quedan en `demo-credentials.txt`.

**Validación:** 124 pruebas automáticas con SQLite. Consulta [VALIDACION.md](VALIDACION.md) y [CAMBIOS-CICC.md](CAMBIOS-CICC.md).

## Inicio rápido (Windows PowerShell)

Instala Python 3.12 y PostgreSQL. Desde esta carpeta:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Crear primero una base PostgreSQL y un usuario con acceso:
$env:PGDATABASE='qahub'
$env:PGUSER='qahub'
$env:PGPASSWORD='tu-clave-local'
$env:PGHOST='localhost'
$env:DJANGO_SECRET_KEY='reemplazar-con-un-secreto-aleatorio'
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Abre http://127.0.0.1:8000. Para una demostración sin instalar PostgreSQL, establece `$env:QA_SQLITE='1'` antes de migrar. Esta alternativa usa SQLite exclusivamente para demostración y pruebas; la configuración por defecto es PostgreSQL.

Cuentas ficticias: `admin` (administra), `ana` (participa), `diego` (edita contenido) y `lucia` (gestiona evaluaciones y consulta reportes). `seed_demo` genera contraseñas aleatorias para las cuentas nuevas y las guarda en `demo-credentials.txt` (excluido del repositorio); con `--password` o `DEMO_PASSWORD` se fija una contraseña común y con `--reset-passwords` se regeneran las de cuentas existentes. La pantalla de acceso solo indica dónde está el archivo con `DEBUG=1` o `SHOW_DEMO_CREDENTIALS=1`. El comando es idempotente y conserva contraseñas existentes. Nunca ejecutes seed en producción.

## Variables de entorno

| Variable | Uso |
|---|---|
| `DEBUG` | `1` (por defecto en local) o `0`. En Vercel el valor por defecto es `0`. |
| `DJANGO_SECRET_KEY` | Obligatoria cuando `DEBUG=0`; la aplicación no arranca con el secreto de desarrollo. |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_ORIGINS` | Hosts y orígenes adicionales, separados por comas. |
| `DJANGO_SSL_REDIRECT` | `0` si un proxy ya redirige a HTTPS (con `DEBUG=0` se redirige por defecto). |
| `SHOW_DEMO_CREDENTIALS` | `1` muestra las cuentas demo en el login (por defecto, solo con `DEBUG=1`). |
| `QA_SQLITE`, `PG*` | Base SQLite de demostración o conexión PostgreSQL. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Correo SMTP para recuperar contraseñas y avisar resultados. Sin `EMAIL_HOST` los mensajes se imprimen en la consola del servidor. |
| `SITE_URL` | Dirección pública del sitio, usada en los enlaces de los correos de resultado. |
| `DEMO_PASSWORD` | Contraseña común para las cuentas demo nuevas (solo para demostraciones locales). |

Con `DEBUG=0` se activan cookies seguras, redirección HTTPS y HSTS. Tras 5 accesos fallidos por usuario y dirección, el acceso se bloquea 15 minutos. La limitación usa la caché local del proceso: con varios procesos o instancias conviene configurar una caché compartida.

## Tareas programadas

`python manage.py close_expired` califica y cierra los intentos cuyo tiempo venció, y envía el aviso por correo a quien tenga uno registrado. Ejecútalo cada pocos minutos con cron o con el Programador de tareas de Windows. Sin tarea programada, un intento vencido se cierra de todos modos cuando su dueño lo abre o cuando alguien guarda o inicia otro.

`python manage.py notify_assessments` envía por correo, una sola vez por persona, el aviso de las evaluaciones asignadas a su grupo que ya están abiertas y el recordatorio de las que cierran en menos de 48 horas (no avisa a quien ya la terminó). Ejecútalo cada hora.

`python manage.py export_weeks` copia el contenido de las 17 semanas de los cursos a la base de datos para editarlas desde el administrador (modelo «Semanas de curso»); una semana guardada sustituye al archivo incluido. Con `--overwrite` se vuelven a copiar desde los archivos.

## Qué puedes probar

1. Ingresa como ana; busca «batch», filtra por área y tipo con los botones, ordena y abre la versión 2 de una guía. Descarga el archivo protegido y marca recursos como favoritos con la estrella.
2. Abre rutas, entra a lecciones y completa una: pasa a la siguiente y el avance por ruta y el panel se actualizan.
3. Inicia una evaluación (si tiene grupos asignados o fechas de apertura y cierre, solo la ven y la inician quienes corresponda). Responde, espera el indicador de guardado y recarga: la selección se recupera. Usa el mapa de preguntas, marca dudas, finaliza con el resumen y revisa puntaje, tiempo, intentos previos y explicación. Puedes reintentar. Al aprobar se emite un certificado con código, verificable en `/certificate/<código>/` y apto para imprimir o guardar como PDF desde el navegador. El desglose por tema usa el campo «tema» de cada pregunta.
4. Como lucia, crea y edita preguntas de selección única, múltiple, verdadero/falso y respuesta corta con vista previa desde «Banco de preguntas», o descarga la plantilla (con la columna opcional `tema`) e impórtala. Una fila inválida debe rechazar todo el lote. Exporta resultados a Excel con filtros por usuario, evaluación y fechas desde Reportes.
5. Como admin, gestiona recursos, versiones, usuarios y grupos desde los enlaces al administrador Django. Revisa auditoría y exporta contenido.
6. Como ana, intenta entrar a `/p/users/` o descargar `/report.xlsx`: debe responder 403.

## Pruebas

```powershell
$env:QA_SQLITE='1'
python manage.py check
python manage.py test hub -v 2
```

Las 124 pruebas cubren acceso por rol, pantallas, menú por permisos, recuperación y congelación de intentos, cálculo de notas, intento único y límite de intentos, aislamiento entre usuarios, expiración, respuestas inválidas, progreso, favoritos, paginación, búsqueda, descargas protegidas, Excel (errores por fila, fórmulas neutralizadas, rollback), respaldo, bloqueo de acceso, validación de ajustes de producción, editor de preguntas, temas, certificados, cohortes, correos, recuperación de contraseña, semanas de curso y reproducción de video por rangos, tipos de pregunta, sorteo por tema, comprobaciones de lección, etiquetas, subida de versiones, perfil, gráficos de reportes, filtros y CSV de auditoría, restauración web y avisos de asignación y plazo. Para estilo ejecuta `pip install -r requirements-dev.txt`, `ruff format --check config hub manage.py` y `ruff check config hub manage.py`; el flujo `.github/workflows/ci.yml` lo hace en cada push. Para verificar PostgreSQL, elimina QA_SQLITE, configura una base de pruebas y ejecuta el mismo comando con un usuario autorizado a crear bases. El servidor de desarrollo es para revisión local.

## Límites del prototipo

- Videoteca navegable con fichas y referencias públicas. Un editor puede adjuntar un archivo .mp4, .webm u .ogg a una versión del recurso y se reproduce dentro de la ficha (con avance y retroceso). Los adjuntos admiten solo extensiones comunes y un máximo de 200 MB; no se transcodifica ni se generan miniaturas.
- Los recursos, rutas, lecciones, usuarios y roles se administran con Django Admin. Las preguntas tienen editor propio con vista previa (cuatro tipos) y los editores pueden subir versiones de un recurso desde su ficha; no hay editor visual para el resto de entidades. Las comprobaciones de lección se editan en el administrador (dentro de cada lección).
- Tipos de pregunta: selección única, selección múltiple (hay que marcar exactamente las correctas, sin puntaje parcial), verdadero/falso y respuesta corta (se ignoran mayúsculas, acentos y espacios repetidos; solo coincidencia exacta con las respuestas aceptadas). La importación por Excel solo crea preguntas de selección única. Con «Preguntas por intento» una evaluación sortea esa cantidad del banco repartida entre los temas.
- Configuración muestra parámetros reales; infraestructura se cambia por variables de entorno, evaluaciones por el administrador.
- Respaldo web exporta contenido, grupos y usuarios (sin contraseñas) en JSON que un superusuario puede restaurar desde la pantalla de Respaldos (sobrescribe objetos con el mismo ID, conserva los usuarios existentes y revierte todo si algo falla) o con `loaddata`; el respaldo completo es una operación de infraestructura documentada en ARQUITECTURA.md. En la demo de Vercel los cambios no persisten entre despliegues (SQLite en `/tmp`).
- Catálogos publicados visibles a todos los participantes autenticados. Mainframe/Distribuido son filtros, no barreras de autorización. Las evaluaciones sí pueden limitarse a grupos y a una ventana de fechas.
- Cada intento guarda una copia de sus preguntas al iniciar, así que editar el banco no altera intentos en curso ni notas históricas. El límite de intentos es por evaluación (0 = sin límite).
- Los certificados son constancias internas con código verificable; la página de verificación es pública y muestra el nombre de la persona, la evaluación, el puntaje y la fecha. No son una certificación oficial ni llevan firma digital.
- El correo depende de un servidor SMTP que debes configurar. La recuperación de contraseña no limita solicitudes repetidas y requiere que la cuenta tenga un correo registrado.
- El contenido HTML de las semanas editadas en el administrador se muestra sin escapar: solo editores de confianza deben modificarlo.
- Modo oscuro (botón del encabezado, recuerda la elección y respeta la preferencia del sistema): cubre las pantallas principales, pero no se revisó con capturas de pantalla en todos los navegadores.
- No contiene SSO, autenticación en dos pasos ni supervisión antifraude.

Consulta [DISEÑO.md](DISEÑO.md) para navegación, pantallas y estilos, y [ARQUITECTURA.md](ARQUITECTURA.md) para datos, permisos, seguridad y respaldos.
