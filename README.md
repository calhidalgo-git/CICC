# CICC — Centro Integral de Conocimiento de Calidad

Ampliación del ZIP original, con 32 recursos, 16 lecciones y búsqueda global de recursos publicados, academia, rutas y evaluaciones. Incluye conocimiento del área, ambiente de certificación, mapa conceptual navegable, Mainframe, Distribuido, ciclo de vida y pruebas, QA/ClearQuest, procedimientos, incidentes y glosario. Todos los escenarios y accesos son ficticios.

**Windows, demo sin PostgreSQL:** extrae el ZIP y ejecuta `powershell -ExecutionPolicy Bypass -File .\START-DEMO.ps1` desde la carpeta `cicc`. Consulta [INSTRUCCIONES-WINDOWS.md](INSTRUCCIONES-WINDOWS.md). Acceso: `admin` / `DemoQA!2026`.

**Validación CICC:** 12 pruebas aprobadas con SQLite. Consulta [VALIDACION.md](VALIDACION.md) y [CAMBIOS-CICC.md](CAMBIOS-CICC.md). El ambiente de certificación es formativo y ClearQuest se describe sin integración. La aplicación solo requiere Python y librerías abiertas; no requiere los productos comerciales estudiados.


Prototipo Django navegable en español para personal QA Mainframe y Distribuido. Todas las herramientas son gratuitas y de código abierto. No requiere servicios de pago ni conexión para su interfaz: Bootstrap y Chart.js se incluyen localmente.

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

Credenciales ficticias: `admin`, `ana`, `diego`, `lucia`, todos con contraseña `DemoQA!2026`. admin administra; ana participa; diego edita contenido; lucia gestiona evaluaciones y consulta reportes. El comando seed es idempotente y conserva contraseñas existentes. Nunca ejecutes seed en producción.

## Qué puedes probar

1. Ingresa como ana; busca «batch», filtra Mainframe y abre la versión 2 de una guía. Descarga el archivo protegido.
2. Abre rutas, entra a lecciones y completa una. Comprueba el contador del dashboard.
3. Inicia una evaluación. Responde, espera el indicador de guardado y recarga: la selección se recupera. Finaliza y revisa puntaje y explicación.
4. Como lucia, descarga la plantilla del banco de preguntas e impórtala. Una fila inválida debe rechazar todo el lote. Exporta resultados a Excel.
5. Como admin, gestiona recursos, versiones, usuarios y grupos desde los enlaces al administrador Django. Revisa auditoría y exporta contenido.
6. Como ana, intenta entrar a `/p/users/` o descargar `/report.xlsx`: debe responder 403.

## Pruebas

```powershell
$env:QA_SQLITE='1'
python manage.py check
python manage.py test hub -v 2
```

Las pruebas cubren acceso por rol, pantallas, recuperación de intentos, cálculo de notas, aislamiento entre usuarios, expiración, respuestas inválidas, progreso idempotente, descargas protegidas, búsqueda, Excel y rollback de importación. Para verificar PostgreSQL, elimina QA_SQLITE, configura una base de pruebas y ejecuta el mismo comando con un usuario autorizado a crear bases. El servidor de desarrollo es para revisión local.

## Límites del prototipo

- Videoteca navegable con fichas y referencias públicas; no se adjuntan grabaciones. Puedes adjuntar archivos desde versiones en el administrador. El reproductor de video local es una extensión pendiente.
- CRUD de recursos, rutas, lecciones, preguntas, usuarios y roles mediante Django Admin. No se ha creado un editor visual alternativo para cada entidad.
- Configuración muestra parámetros reales; infraestructura se cambia por variables de entorno, evaluaciones por el administrador.
- Respaldo web exporta contenido JSON; el respaldo completo y su restauración son operaciones de infraestructura documentadas en ARQUITECTURA.md.
- Catálogos publicados visibles a todos los participantes autenticados. Mainframe/Distribuido son filtros, no barreras de autorización.
- Cada evaluación debe mantener sus preguntas y opciones estables durante los intentos. La congelación de un examen por versión, límites de intentos y asignación por cohortes quedan para una fase posterior.
- No contiene correo, recuperación de contraseña, SSO, supervisión antifraude ni emisión de certificados.

Consulta [DISEÑO.md](DISEÑO.md) para navegación, pantallas y estilos, y [ARQUITECTURA.md](ARQUITECTURA.md) para datos, permisos, seguridad y respaldos.
