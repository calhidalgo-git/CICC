$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.12 y vuelve a ejecutar.' }
}
& .venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
$env:QA_SQLITE='1'
& .venv/Scripts/python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Error al preparar la base demo.' }
& .venv/Scripts/python.exe manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Error al cargar los datos ficticios.' }
Write-Host 'Abre http://127.0.0.1:8000 · admin / DemoQA!2026'
& .venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
