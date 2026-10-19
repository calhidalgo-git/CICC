# CICC — Inicio en Windows

1. Instala Python 3.12 desde python.org y activa la opción de añadir Python al PATH.
2. Extrae CICC.zip en una carpeta de tu equipo. Abre PowerShell dentro de la carpeta `cicc` que contiene `manage.py`.
3. Ejecuta `powershell -ExecutionPolicy Bypass -File .\START-DEMO.ps1`. El permiso de ejecución se aplica solamente a ese proceso. Opciones: `-Port 8001` cambia el puerto, `-NoBrowser` no abre el navegador y `-Reset` borra la base demo y las credenciales para empezar de cero.
4. La primera ejecución necesita Internet para instalar librerías abiertas (después solo se reinstalan si cambia requirements.txt). Se exige Python 3.12 o superior. Se crea un entorno virtual local, se aplican migraciones y se cargan datos ficticios en SQLite.
5. Se abre http://127.0.0.1:8000 en tu navegador. Las cuentas son `admin` (administrador), `ana` (participante), `diego` (editor) y `lucia` (evaluador); sus contraseñas se generan al preparar la demo y están en el archivo `demo-credentials.txt` de la carpeta del proyecto.
6. Detén el servidor con Ctrl+C. Vuelve a ejecutar el mismo archivo para continuar: conserva usuarios, progreso e intentos. El catálogo ficticio CICC se actualiza al ejecutar seed_demo; no edites esos ejemplos si deseas conservarlos entre cargas.

## Ejecución manual

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:QA_SQLITE='1'
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py seed_demo
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

## Pruebas

```powershell
$env:QA_SQLITE='1'
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py test hub -v 2
```

Si `python` abre Microsoft Store, revisa la instalación y los alias de ejecución de Windows. Si el puerto está ocupado, usa `runserver 127.0.0.1:8001 --noreload` y abre ese puerto. Si falla una descarga, verifica acceso a PyPI y vuelve a ejecutar. No requiere Excel instalado para importar o exportar .xlsx.

La demo no necesita Mainframe, Oracle, WebSphere ni ClearQuest: son temas formativos. El ambiente de certificación es un módulo educativo; no se conecta a infraestructura real. Para PostgreSQL y las limitaciones del prototipo consulta README.md.
