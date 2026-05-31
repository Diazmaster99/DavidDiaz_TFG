# Build release

Este directorio contiene **los dos artefactos de distribución** del TFG:

| Archivo               | Para qué sirve                                                          |
|-----------------------|-------------------------------------------------------------------------|
| `build_portable.ps1`  | Genera la carpeta y el `.7z` portable (sin instalación).                |
| `setup.iss`           | Genera el instalador `setup.exe` (Inno Setup 6) a partir de esa carpeta.|

Salida (no incluida en el repo):

```
_build_release/
  cache/                                python-*.zip, node-*.zip, get-pip.py
  dist/
    DavidDiaz_TFG_portable/             carpeta lista para zipear/instalar
    DavidDiaz_TFG_portable.7z           paquete portable final
    DavidDiaz_TFG_setup.exe             instalador Windows final
```

---

## 1. Generar el paquete portable

Requisitos en el equipo que **construye** el paquete:

- Windows x64.
- PowerShell 5+.
- Acceso a Internet (la primera vez baja Python embeddable y Node portable a
  `cache/`; siguientes ejecuciones reutilizan la caché).
- 7-Zip instalado (para crear el `.7z` final;
  si falta, el script avisa y deja la carpeta sin comprimir).
- El fork del servidor en `pokemon-showdown/` debe estar **compilado**
  (`npm install && node build` dentro de esa carpeta) antes de empaquetar:
  el script lo copia tal cual.

Comando (desde la raíz del proyecto):

```powershell
powershell -ExecutionPolicy Bypass -File _build_release\build_portable.ps1
```

Opciones útiles:

```powershell
# No descargar runtimes si ya están en cache/
-SkipDownload

# Omitir los modelos entrenados (paquete mucho mas ligero)
-SkipModels

# Versiones distintas
-PyVersion 3.11.9
-NodeVersion 20.18.0
```

El script ejecuta, por orden:

1. Descarga (o reutiliza) Python embeddable y Node portable en `cache/`.
2. Crea `dist/DavidDiaz_TFG_portable/python/` con el Python embebido y activa
   `import site` en su `python311._pth`.
3. Instala `pip` con `get-pip.py` y crea un **venv con `--copies`** en
   `runtime/venv/`, donde instala `requirements.txt` (`torch`, `sb3-contrib`,
   `poke-env`, …).
4. Extrae Node a `runtime/node/`.
5. Copia el fork `pokemon-showdown/` con su `node_modules/` y `dist/`.
6. Copia `src/`, `teams/`, `models/` (salvo `-SkipModels`) y los scripts sueltos
   de la raíz (`play.py`, `train_*.py`, etc.) a `app/`.
7. Escribe los lanzadores `START_servidor.bat`, `START_bot.bat`,
   `ABRIR_shell.bat` y un `LEEME.txt` con instrucciones.
8. Comprime todo a `dist/DavidDiaz_TFG_portable.7z` con compresión máxima.

Tiempo aproximado en una build limpia: **5-10 min** (la primera vez, dominada
por la descarga de PyTorch).

---

## 2. Generar el instalador Windows

Requisitos:

- [Inno Setup 6](https://jrsoftware.org/isinfo.php) instalado.
- La carpeta `dist/DavidDiaz_TFG_portable/` ya generada por el paso 1.

Compilación por GUI:

1. Abrir `setup.iss` con Inno Setup.
2. Pulsar **Compile** (F9).

Compilación por línea de comandos (desde la raíz del proyecto):

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" _build_release\setup.iss
```

Salida: `_build_release/dist/DavidDiaz_TFG_setup.exe`.

El instalador:

- Se instala por defecto en `C:\Program Files\DavidDiaz_TFG`.
- Crea grupo en el menú Inicio con accesos directos a "Arrancar servidor",
  "Lanzar bot", "Shell del bot" y "Desinstalar".
- Ofrece (opcional) accesos directos en el escritorio.
- Al desinstalar, borra también `logs/`, `databases/` y `__pycache__/`
  generados durante el uso.

---

## 3. Qué entregar en la rúbrica

La rúbrica del TFG pide **uno** de los dos formatos. Aquí se generan los dos
para tener margen:

- **Portable** → `dist/DavidDiaz_TFG_portable.7z`
  (descomprimir y doble clic en los `.bat`; no requiere instalación).
- **Instalador** → `dist/DavidDiaz_TFG_setup.exe`
  (siguiente-siguiente-siguiente).

Ambos son **autocontenidos**: el equipo de destino no necesita tener instalado
Python, Node, ni ninguna dependencia previa.
