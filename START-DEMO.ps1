<#
.SYNOPSIS
  Prepara y arranca la demo de CICC con SQLite (sin PostgreSQL).
.PARAMETER Port
  Puerto local (por defecto 8000).
.PARAMETER Reset
  Borra la base demo y las credenciales generadas, y vuelve a crearlas desde cero.
.PARAMETER NoBrowser
  No abre el navegador automáticamente.
#>
param(
    [int]$Port = 8000,
    [switch]$Reset,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Step([string]$Message, [scriptblock]$Action) {
    & $Action
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

# 1. Python 3.12 o superior
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'No se encontró Python. Instala Python 3.12 o superior desde python.org y marca la opción "Add python.exe to PATH".'
}
$found = [version](& python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
if ($found -lt [version]'3.12') {
    throw "Se necesita Python 3.12 o superior; esta instalación es la $found."
}

# 2. Entorno virtual y dependencias (solo se reinstalan si cambió requirements.txt)
$venvPython = '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-Step 'No se pudo crear el entorno virtual.' { python -m venv .venv }
}
$stamp = '.venv/requirements.sha256'
$hash = (Get-FileHash -LiteralPath 'requirements.txt' -Algorithm SHA256).Hash
if (-not (Test-Path -LiteralPath $stamp) -or (Get-Content -LiteralPath $stamp -Raw).Trim() -ne $hash) {
    Write-Host 'Instalando dependencias (requiere Internet la primera vez)...'
    Invoke-Step 'No se pudieron instalar las dependencias.' { & $venvPython -m pip install -r requirements.txt }
    Set-Content -LiteralPath $stamp -Value $hash
}

# 3. Base de datos demo
$env:QA_SQLITE = '1'
if ($Reset) {
    Write-Warning 'Se borrarán la base demo (usuarios, progreso e intentos) y demo-credentials.txt.'
    Remove-Item -LiteralPath 'demo.sqlite3', 'demo-credentials.txt' -Force -ErrorAction SilentlyContinue
}
Invoke-Step 'Error al preparar la base demo.' { & $venvPython manage.py migrate }
Invoke-Step 'Error al cargar los datos ficticios.' { & $venvPython manage.py seed_demo }

# 4. Puerto libre
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "El puerto $Port está ocupado. Cierra el otro programa o ejecuta: .\START-DEMO.ps1 -Port $($Port + 1)"
}

$url = "http://127.0.0.1:$Port"
Write-Host ''
Write-Host "Abre $url" -ForegroundColor Green
if (Test-Path -LiteralPath 'demo-credentials.txt') {
    Write-Host 'Usuarios y contraseñas de la demo: demo-credentials.txt (admin, ana, diego y lucia).'
} else {
    Write-Host 'Las cuentas demo ya existían; sus contraseñas no se muestran. Usa -Reset para generarlas de nuevo.'
}
Write-Host 'Detén el servidor con Ctrl+C.'
if (-not $NoBrowser) {
    Start-Job -ScriptBlock { param($target) Start-Sleep -Seconds 3; Start-Process $target } -ArgumentList $url | Out-Null
}
& $venvPython manage.py runserver "127.0.0.1:$Port" --noreload
