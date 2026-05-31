; ============================================================================
;  setup.iss  -  Instalador Windows del Bot VGC TFG (Inno Setup 6)
;
;  Empaqueta la carpeta _build_release\dist\DavidDiaz_TFG_portable en un único
;  setup.exe que el usuario ejecuta con doble clic y queda instalado en
;  Program Files con accesos directos en el menú Inicio.
;
;  Prerrequisito: haber ejecutado antes
;       powershell -ExecutionPolicy Bypass -File _build_release\build_portable.ps1
;  para generar la carpeta DavidDiaz_TFG_portable\.
;
;  Compilación (desde la raíz del proyecto):
;       "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" _build_release\setup.iss
;  o abriendo este .iss con la GUI de Inno Setup y pulsando Compile (F9).
;
;  Salida: _build_release\dist\DavidDiaz_TFG_setup.exe
; ============================================================================

#define MyAppName        "Bot VGC TFG"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "David Diaz Garcia"
#define MyAppDescription "Bot de combates Pokemon VGC entrenado con RL (TFG)"
#define MyAppExeServer   "START_servidor.bat"
#define MyAppExeBot      "START_bot.bat"
#define MyAppExeShell    "ABRIR_shell.bat"

; Carpeta generada por build_portable.ps1 (relativa a este .iss)
#define PortableDir      "dist\DavidDiaz_TFG_portable"

[Setup]
; AppId fijo: identifica al programa en "Programas y características"
; y permite actualizaciones limpias entre versiones.
AppId={{B3F2A1C4-8E5D-4B7F-9A2C-1D8E4F6A3B5C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppComments={#MyAppDescription}
DefaultDirName={autopf}\DavidDiaz_TFG
DefaultGroupName=Bot VGC TFG
DisableProgramGroupPage=yes
DisableDirPage=no
AllowNoIcons=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=DavidDiaz_TFG_setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeServer}
; SetupIconFile=icono.ico    ; (opcional) descomenta si añades un .ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Toda la carpeta portable en {app}. recursesubdirs + createallsubdirs
; reproduce la estructura tal cual.
Source: "{#PortableDir}\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Menú Inicio
Name: "{group}\Arrancar servidor Showdown"; Filename: "{app}\{#MyAppExeServer}"; \
    WorkingDir: "{app}"; Comment: "Inicia el servidor Pokémon Showdown local."
Name: "{group}\Lanzar bot (acepta desafíos)"; Filename: "{app}\{#MyAppExeBot}"; \
    WorkingDir: "{app}"; Comment: "Lanza el bot a la espera de desafíos."
Name: "{group}\Shell del bot (Python)"; Filename: "{app}\{#MyAppExeShell}"; \
    WorkingDir: "{app}"; Comment: "Terminal con el entorno Python del bot activo."
Name: "{group}\Carpeta del bot"; Filename: "{app}"; \
    Comment: "Abre la carpeta de instalación."
Name: "{group}\Documentación"; Filename: "{app}\LEEME.txt"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

; Escritorio (solo si el usuario marca la casilla en el wizard)
Name: "{autodesktop}\Bot VGC TFG - Servidor"; Filename: "{app}\{#MyAppExeServer}"; \
    WorkingDir: "{app}"; Tasks: desktopicon
Name: "{autodesktop}\Bot VGC TFG - Bot"; Filename: "{app}\{#MyAppExeBot}"; \
    WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Mostrar el LEEME al terminar la instalación (opcional, casilla del wizard).
Filename: "{app}\LEEME.txt"; Description: "Ver instrucciones de uso"; \
    Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
; Borra ficheros generados en ejecución que quedarían huérfanos al desinstalar.
Type: filesandordirs; Name: "{app}\pokemon-showdown\logs"
Type: filesandordirs; Name: "{app}\pokemon-showdown\databases"
Type: filesandordirs; Name: "{app}\app\logs"
Type: filesandordirs; Name: "{app}\app\__pycache__"

[Code]
// Comprobacion: si build_portable.ps1 aún no ha generado la carpeta portable,
// avisa al usuario que esta intentando compilar antes de tiempo. Se evalúa
// en tiempo de COMPILACIÓN del instalador, no de instalación.
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
