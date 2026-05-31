# =============================================================================
#  build_portable.ps1
#  Construye el paquete PORTABLE del bot VGC del TFG.
#
#  Resultado:  _build_release\dist\DavidDiaz_TFG_portable\   (carpeta lista)
#              _build_release\dist\DavidDiaz_TFG_portable.7z (paquete final)
#
#  La carpeta contiene Python embebido + venv con todas las dependencias +
#  Node.js portable + el servidor Pokémon Showdown ya compilado + el código del
#  bot + los modelos entrenados + lanzadores .bat. Se ejecuta sin instalar nada.
#
#  Requisitos en la máquina que CONSTRUYE el paquete:
#    - Windows x64, PowerShell 5+.
#    - Acceso a Internet (descarga Python y Node portables la primera vez).
#    - 7-Zip instalado (para crear el .7z final).  https://www.7-zip.org
#      (si no está, el script avisa y deja solo la carpeta sin comprimir).
#    - El fork del servidor en pokemon-showdown\ ya compilado (`node build`)
#      con su node_modules instalado.
#
#  Uso (desde la raíz del proyecto):
#    powershell -ExecutionPolicy Bypass -File _build_release\build_portable.ps1
#
#  Opciones:
#    -SkipDownload    No vuelve a bajar Python/Node si ya estaban descargados.
#    -SkipModels      No incluye los modelos entrenados (paquete mucho mas ligero).
#    -PyVersion 3.11.9   Versión de Python embeddable a usar.
#    -NodeVersion 20.18.0  Versión de Node portable a usar.
# =============================================================================

[CmdletBinding()]
param(
    [switch]$SkipDownload,
    [switch]$SkipModels,
    [string]$PyVersion = "3.11.9",
    [string]$NodeVersion = "20.18.0"
)

$ErrorActionPreference = "Stop"
$ProgressPreference   = "SilentlyContinue"   # acelera Invoke-WebRequest

# ---------- Rutas base -----------------------------------------------------
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ReleaseDir  = Join-Path $ProjectRoot "_build_release"
$CacheDir    = Join-Path $ReleaseDir "cache"
$DistDir     = Join-Path $ReleaseDir "dist"
$OutName     = "DavidDiaz_TFG_portable"
$OutDir      = Join-Path $DistDir $OutName

New-Item -ItemType Directory -Force -Path $CacheDir, $DistDir | Out-Null

function Section($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Require-Cmd($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: no se encontró '$name' en el PATH.  $hint" -ForegroundColor Red
        exit 1
    }
}

# ---------- 0. Carpeta de salida limpia -----------------------------------
Section "Preparando carpeta de salida"
if (Test-Path $OutDir) {
    Write-Host "  Borrando $OutDir (existía de un build anterior)"
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Write-Host "  Salida: $OutDir"

# ---------- 1. Python embeddable ------------------------------------------
Section "Python embeddable $PyVersion"
$PyZip = Join-Path $CacheDir "python-$PyVersion-embed-amd64.zip"
$PyUrl = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip"
if (-not (Test-Path $PyZip) -or -not $SkipDownload) {
    if (-not (Test-Path $PyZip)) {
        Write-Host "  Descargando $PyUrl"
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip
    } else {
        Write-Host "  Ya cacheado: $PyZip"
    }
}
$PyDir = Join-Path $OutDir "python"
Expand-Archive -Path $PyZip -DestinationPath $PyDir -Force

# Activar 'import site' en el _pth para que el venv funcione.
$Pth = Get-ChildItem -Path $PyDir -Filter "python*._pth" | Select-Object -First 1
if ($Pth) {
    (Get-Content $Pth.FullName) `
        -replace '^\s*#\s*import\s+site', 'import site' `
        | Set-Content -Encoding ASCII $Pth.FullName
    Write-Host "  Activado 'import site' en $($Pth.Name)"
} else {
    Write-Host "AVISO: no se encontró python*._pth en $PyDir" -ForegroundColor Yellow
}

# pip no viene en el embeddable: lo añadimos via get-pip.
$GetPip = Join-Path $CacheDir "get-pip.py"
if (-not (Test-Path $GetPip)) {
    Write-Host "  Descargando get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip
}
$PyExe = Join-Path $PyDir "python.exe"
Write-Host "  Instalando pip en el Python embebido"
& $PyExe $GetPip --no-warn-script-location | Out-Null

# ---------- 2. Crear venv del proyecto con --copies -----------------------
Section "Entorno virtual con dependencias del bot"
$VenvDir = Join-Path $OutDir "runtime\venv"
New-Item -ItemType Directory -Force -Path (Split-Path $VenvDir) | Out-Null
& $PyExe -m venv --copies $VenvDir
$VenvPy  = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
& $VenvPy -m pip install --upgrade pip wheel setuptools | Out-Null

$Req = Join-Path $ProjectRoot "requirements.txt"
if (-not (Test-Path $Req)) {
    Write-Host "ERROR: no existe $Req" -ForegroundColor Red
    exit 1
}
Write-Host "  Instalando dependencias de requirements.txt (puede tardar varios minutos)"
& $VenvPip install -r $Req
if ($LASTEXITCODE -ne 0) { exit 1 }

# ---------- 3. Node.js portable -------------------------------------------
Section "Node.js portable $NodeVersion"
$NodeZip = Join-Path $CacheDir "node-v$NodeVersion-win-x64.zip"
$NodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x64.zip"
if (-not (Test-Path $NodeZip)) {
    Write-Host "  Descargando $NodeUrl"
    Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeZip
} else {
    Write-Host "  Ya cacheado: $NodeZip"
}
$NodeOut = Join-Path $OutDir "runtime\node"
Expand-Archive -Path $NodeZip -DestinationPath (Split-Path $NodeOut) -Force
$Extracted = Join-Path (Split-Path $NodeOut) "node-v$NodeVersion-win-x64"
if (Test-Path $NodeOut) { Remove-Item -Recurse -Force $NodeOut }
Rename-Item $Extracted $NodeOut

# ---------- 4. Servidor Pokémon Showdown ----------------------------------
Section "Servidor Pokémon Showdown (fork del proyecto)"
$PsSrc = Join-Path $ProjectRoot "pokemon-showdown"
if (-not (Test-Path $PsSrc)) {
    Write-Host "ERROR: no se encontró $PsSrc" -ForegroundColor Red
    Write-Host "Clona el fork del servidor antes de empaquetar." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $PsSrc "node_modules"))) {
    Write-Host "AVISO: pokemon-showdown\node_modules no existe." -ForegroundColor Yellow
    Write-Host "       El bot no arrancará sin instalar dependencias." -ForegroundColor Yellow
    Write-Host "       Ejecuta primero:  cd pokemon-showdown ; npm install ; node build" -ForegroundColor Yellow
}
$PsOut = Join-Path $OutDir "pokemon-showdown"
Write-Host "  Copiando con robocopy (excluye .git, logs, databases)..."
$rcArgs = @(
    $PsSrc, $PsOut,
    "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
    "/XD", ".git", "logs", "databases",
    "/XF", "*.log"
)
& robocopy @rcArgs | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host "ERROR: robocopy falló ($LASTEXITCODE)" -ForegroundColor Red; exit 1 }

# ---------- 5. Código del bot --------------------------------------------
Section "Código del bot y recursos"
$AppOut = Join-Path $OutDir "app"
New-Item -ItemType Directory -Force -Path $AppOut | Out-Null

# Carpetas a incluir tal cual
$includeDirs = @("src", "teams")
foreach ($d in $includeDirs) {
    $srcDir = Join-Path $ProjectRoot $d
    if (Test-Path $srcDir) {
        $dstDir = Join-Path $AppOut $d
        Write-Host "  $d\"
        & robocopy $srcDir $dstDir /E /NFL /NDL /NJH /NJS /NP /XD __pycache__ | Out-Null
    }
}

# Modelos (opcional)
$ModelsSrc = Join-Path $ProjectRoot "models"
if (-not $SkipModels -and (Test-Path $ModelsSrc)) {
    Write-Host "  models\"
    & robocopy $ModelsSrc (Join-Path $AppOut "models") /E /NFL /NDL /NJH /NJS /NP | Out-Null
} elseif ($SkipModels) {
    Write-Host "  models\  (omitido por -SkipModels)"
}

# Scripts sueltos en la raíz
$rootScripts = @(
    "play.py", "train_singles.py", "train_doubles.py",
    "battle_models.py", "selfplay_from.py", "plot_metrics.py",
    "check_teams.py", "patch_server_formats.py", "test_env.py",
    "requirements.txt", "README.md", "INSTALACION.txt", "COMANDOS.txt"
)
foreach ($f in $rootScripts) {
    $p = Join-Path $ProjectRoot $f
    if (Test-Path $p) {
        Copy-Item $p (Join-Path $AppOut $f)
        Write-Host "  $f"
    }
}

# ---------- 6. Lanzadores .bat -------------------------------------------
Section "Lanzadores"

$StartServer = @'
@echo off
title Servidor Pokemon Showdown - Bot VGC TFG
cd /d "%~dp0pokemon-showdown"
echo Arrancando servidor en http://localhost:8000  (Ctrl+C para parar)
echo.
"%~dp0runtime\node\node.exe" pokemon-showdown start --no-security
pause
'@
Set-Content -Path (Join-Path $OutDir "START_servidor.bat") -Value $StartServer -Encoding ASCII

$StartBot = @'
@echo off
title Bot VGC TFG - aceptando desafios
cd /d "%~dp0app"
echo.
echo Lanzando el bot. Abre http://localhost:8000 en el navegador,
echo elige el formato y reta al usuario "MiBot".
echo (El servidor debe estar arrancado con START_servidor.bat).
echo.
"%~dp0runtime\venv\Scripts\python.exe" play.py ^
    --mode doubles --username MiBot --run_id 1 ^
    --format gen9vgc2026regi ^
    --team teams\vgc\reg_i
pause
'@
Set-Content -Path (Join-Path $OutDir "START_bot.bat") -Value $StartBot -Encoding ASCII

$StartShell = @'
@echo off
rem Abre un Símbolo del sistema con el venv del bot ya activado,
rem por si quieres lanzar train_singles.py, battle_models.py, etc.
title Shell del bot (venv activado)
cd /d "%~dp0app"
"%~dp0runtime\venv\Scripts\activate.bat"
cmd /k
'@
Set-Content -Path (Join-Path $OutDir "ABRIR_shell.bat") -Value $StartShell -Encoding ASCII

$Readme = @'
================================================================
  BOT VGC TFG - Distribución portable
  David Díaz García - TFG
================================================================

REQUISITOS DEL EQUIPO DE DESTINO
  - Windows 10/11 x64.
  - No hace falta instalar Python, Node ni nada: TODO está incluido.

CÓMO USAR
  1) Doble clic en START_servidor.bat
     (arranca el servidor Pokémon Showdown en localhost:8000).
  2) Doble clic en START_bot.bat
     (lanza el bot, queda a la espera de desafíos como "MiBot").
  3) Abrir http://localhost:8000 en el navegador, elegir el
     formato (por defecto VGC 2026 Reg I) y desafiar a "MiBot".

LANZAR OTROS COMANDOS
  Doble clic en ABRIR_shell.bat abre un terminal con el entorno
  Python del bot ya activo. Desde ahí:
     python train_doubles.py --help
     python battle_models.py --help
     python plot_metrics.py
     ...

DOCUMENTACIÓN
  - INSTALACION.txt  -  Si quisieras montar el proyecto desde cero.
  - COMANDOS.txt     -  Recetario de todos los comandos del proyecto.
  - README.md        -  Visión general del bot.
  - app\models\      -  Modelos entrenados ya incluidos.
  - app\teams\       -  Equipos VGC.

================================================================
'@
Set-Content -Path (Join-Path $OutDir "LEEME.txt") -Value $Readme -Encoding UTF8

Write-Host "  START_servidor.bat / START_bot.bat / ABRIR_shell.bat / LEEME.txt"

# ---------- 7. Compresión 7z ---------------------------------------------
Section "Comprimiendo paquete final"
$SevenZip = $null
foreach ($p in @("C:\Program Files\7-Zip\7z.exe", "C:\Program Files (x86)\7-Zip\7z.exe")) {
    if (Test-Path $p) { $SevenZip = $p; break }
}
if (-not $SevenZip -and (Get-Command 7z -ErrorAction SilentlyContinue)) {
    $SevenZip = "7z"
}

$ArchivePath = Join-Path $DistDir "$OutName.7z"
if (Test-Path $ArchivePath) { Remove-Item -Force $ArchivePath }

if ($SevenZip) {
    Write-Host "  Usando 7-Zip: $SevenZip"
    Push-Location $DistDir
    & $SevenZip a -t7z -mx=9 -ms=on $ArchivePath $OutName | Out-Null
    Pop-Location
    if (Test-Path $ArchivePath) {
        $sizeMB = [math]::Round((Get-Item $ArchivePath).Length / 1MB, 1)
        Write-Host ("  Generado: $ArchivePath  ({0} MB)" -f $sizeMB) -ForegroundColor Green
    } else {
        Write-Host "ERROR: 7z no generó el archivo." -ForegroundColor Red
    }
} else {
    Write-Host "AVISO: 7-Zip no encontrado. Solo se ha generado la carpeta." -ForegroundColor Yellow
    Write-Host "       Instala 7-Zip y vuelve a lanzar, o comprime $OutDir a mano." -ForegroundColor Yellow
}

Section "Hecho"
Write-Host "Carpeta portable:  $OutDir"
if (Test-Path $ArchivePath) { Write-Host "Archivo 7z:        $ArchivePath" }
Write-Host ""
Write-Host "Para crear ademas el instalador Windows:"
Write-Host "  - Instala Inno Setup 6 (https://jrsoftware.org/isinfo.php)"
Write-Host "  - Compila _build_release\setup.iss con ISCC"
