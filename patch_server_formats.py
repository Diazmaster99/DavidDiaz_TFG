# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Añade al servidor FORKEADO (pokemon-showdown/) todos los formatos VGC actuales
del repositorio OFICIAL de Pokémon Showdown que aún no estén en el fork.

Así el fork mantiene sus arreglos de estabilidad (gestión de salas/timeouts)
y además tiene los formatos VGC al día (por ejemplo gen9vgc2026regi, regf, Bo3...).

Qué hace:
  1. Descarga config/formats.ts del repo oficial (smogon/pokemon-showdown).
  2. Extrae las entradas de formato cuyo nombre contiene "VGC".
  3. Compara por ID con las que ya tiene el fork y añade SOLO las que faltan.
  4. Reescribe el config/formats.ts del fork.

Después hay que recompilar y reiniciar el servidor:
    cd pokemon-showdown
    node build
    node pokemon-showdown start --no-security

Uso:
    python patch_server_formats.py
    python patch_server_formats.py --dry-run         (solo muestra qué añadiría)
"""

import argparse
import re
import urllib.request
from pathlib import Path

OFFICIAL_URL = (
    "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/"
    "config/formats.ts"
)
FORK_FORMATS = Path("pokemon-showdown/config/formats.ts")
# Ancla del fork tras la cual insertamos los formatos VGC nuevos.
ANCHOR_NAME = '[Gen 9] VGC 2025 Reg J'


def to_id(name: str) -> str:
    """Replica toID() de Showdown: minúsculas y solo alfanumérico."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def split_top_level_blocks(text: str) -> list[str]:
    """
    Trocea el array de formatos en bloques de nivel superior: cada entrada
    '{ ... }' indentada con un tab. Devuelve la lista de bloques (texto).
    """
    lines = text.split("\n")
    blocks = []
    current = None
    for line in lines:
        if line == "\t{":
            current = [line]
        elif current is not None:
            current.append(line)
            if line == "\t}," or line == "\t}":
                blocks.append("\n".join(current))
                current = None
    return blocks


def block_name(block: str) -> str | None:
    m = re.search(r'name:\s*"([^"]+)"', block)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra qué formatos añadiría, sin escribir.")
    parser.add_argument("--url", default=OFFICIAL_URL,
                        help="URL del formats.ts oficial.")
    parser.add_argument("--fork", default=str(FORK_FORMATS),
                        help="Ruta al formats.ts del fork.")
    args = parser.parse_args()

    fork_path = Path(args.fork)
    if not fork_path.exists():
        raise FileNotFoundError(
            f"No existe {fork_path}. Ejecuta desde la raíz del proyecto "
            "(donde está la carpeta pokemon-showdown/)."
        )

    print(f"Descargando formatos oficiales de:\n  {args.url}")
    with urllib.request.urlopen(args.url, timeout=30) as resp:
        official = resp.read().decode("utf-8")

    fork_text = fork_path.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in fork_text else "\n"
    # Normalizamos a \n para procesar; restauramos al final.
    fork_work = fork_text.replace("\r\n", "\n")

    # IDs de formato que ya tiene el fork
    fork_ids = set()
    for blk in split_top_level_blocks(fork_work):
        n = block_name(blk)
        if n:
            fork_ids.add(to_id(n))

    # Formatos VGC del oficial que faltan en el fork
    official_blocks = split_top_level_blocks(official.replace("\r\n", "\n"))
    to_add = []
    seen = set()
    for blk in official_blocks:
        n = block_name(blk)
        if not n or "vgc" not in n.lower():
            continue
        fid = to_id(n)
        if fid in fork_ids or fid in seen:
            continue
        seen.add(fid)
        to_add.append((n, fid, blk))

    if not to_add:
        print("\nEl fork ya tiene todos los formatos VGC del oficial. Nada que hacer.")
        return

    print(f"\nFormatos VGC a añadir ({len(to_add)}):")
    for n, fid, _ in to_add:
        print(f"  + {n}   (id: {fid})")

    if args.dry_run:
        print("\n[dry-run] No se ha escrito nada.")
        return

    # Insertar los bloques nuevos tras la entrada ancla del fork
    anchor_idx = fork_work.find(f'name: "{ANCHOR_NAME}"')
    if anchor_idx == -1:
        # Fallback: insertar antes del cierre del array "\n];"
        insert_at = fork_work.rfind("\n];")
        if insert_at == -1:
            raise RuntimeError("No se encontró punto de inserción en el formats.ts del fork.")
        block_end = insert_at
    else:
        # Cierre del bloque ancla: primer "\n\t}," tras el ancla
        close = fork_work.find("\n\t},", anchor_idx)
        block_end = close + len("\n\t},") if close != -1 else fork_work.rfind("\n];")

    insertion = "\n" + "\n".join(blk for _, _, blk in to_add)
    new_text = fork_work[:block_end] + insertion + fork_work[block_end:]

    # Restaurar fin de línea original
    if nl == "\r\n":
        new_text = new_text.replace("\n", "\r\n")
    fork_path.write_text(new_text, encoding="utf-8", newline="")

    print(f"\nAñadidos {len(to_add)} formatos a {fork_path}")
    print("\nAhora recompila y reinicia el servidor:")
    print("    cd pokemon-showdown")
    print("    node build")
    print("    node pokemon-showdown start --no-security")


if __name__ == "__main__":
    main()
