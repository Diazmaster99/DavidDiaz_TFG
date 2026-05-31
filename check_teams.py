# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Valida todos los equipos de una carpeta contra el servidor local.

Para cada fichero .txt:
  1) Comprueba que la sintaxis es correcta (lo parsea poke-env, offline).
  2) Lo prueba contra el servidor en un combate espejo rápido: si el servidor
     acepta el desafío, el equipo es legal para el formato; si lo rechaza
     (desafío que nunca arranca -> timeout), el equipo es ilegal.

Al final reporta cuántos válidos/inválidos y escribe la lista de inválidos en
'equipos_invalidos.txt'.

Uso:
    python check_teams.py --folder teams/vgc/reg_i --format gen9vgc2026regi

Requiere el servidor local corriendo:
    node pokemon-showdown start --no-security
"""

import argparse
import asyncio
import socket
from pathlib import Path

from poke_env.player import RandomPlayer
from poke_env.teambuilder.constant_teambuilder import ConstantTeambuilder

from play import make_server_config


def check_server(port: int):
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect(("localhost", port))
        s.close()
    except (ConnectionRefusedError, TimeoutError, OSError):
        raise RuntimeError(
            f"\n ERROR: No hay servidor Showdown en localhost:{port}\n"
            f" Arranca el servidor:  node pokemon-showdown start --no-security\n"
        )


async def check_teams(folder: str, battle_format: str, port: int,
                      timeout: float, max_teams: int | None):
    check_server(port)
    server = make_server_config(port, official=False)

    files = sorted(Path(folder).glob("*.txt"))
    if not files:
        print(f"No hay ficheros .txt en {folder}")
        return
    if max_teams:
        files = files[:max_teams]
    print(f"Validando {len(files)} equipos de '{folder}' en {battle_format}...\n")

    # Dos jugadores reutilizados; les cambiamos el equipo en cada prueba.
    # Silenciamos el log (incl. el aviso de open team sheets en VGC).
    from src.doubles_env import _SuppressOpenTeamSheetFilter
    ots = _SuppressOpenTeamSheetFilter()
    common = dict(
        battle_format=battle_format,
        server_configuration=server,
        log_level=50,
        max_concurrent_battles=1,
    )
    placeholder = ConstantTeambuilder(files[0].read_text(encoding="utf-8"))
    p1 = RandomPlayer(team=placeholder, **common)
    p2 = RandomPlayer(team=placeholder, **common)
    p1.logger.addFilter(ots)
    p2.logger.addFilter(ots)

    invalid: list[tuple[str, str]] = []
    n_ok = 0

    for i, f in enumerate(files):
        raw = f.read_text(encoding="utf-8")
        # 1) Sintaxis (offline)
        try:
            tb = ConstantTeambuilder(raw)
        except Exception as e:
            invalid.append((f.name, f"sintaxis: {e}"))
            continue

        # 2) Combate espejo contra el servidor
        p1._team = tb
        p2._team = tb
        p1.reset_battles()
        p2.reset_battles()
        started = False
        try:
            await asyncio.wait_for(
                p1.battle_against(p2, n_battles=1), timeout=timeout
            )
            started = True
        except Exception:
            # Si se creó una batalla, el equipo es legal (solo fue lento/cancelado)
            started = len(p1.battles) > 0 or p1.n_finished_battles > 0

        if started:
            n_ok += 1
        else:
            invalid.append((f.name, "rechazado por el servidor (ilegal para el formato)"))

        if (i + 1) % 25 == 0 or (i + 1) == len(files):
            print(f"  {i + 1}/{len(files)} probados | válidos: {n_ok} | inválidos: {len(invalid)}",
                  flush=True)

    print("\n------------------- RESUMEN -------------------")
    print(f"  Equipos válidos:   {n_ok}")
    print(f"  Equipos inválidos: {len(invalid)}")
    if invalid:
        out = Path("equipos_invalidos.txt")
        with out.open("w", encoding="utf-8") as fh:
            for name, reason in invalid:
                fh.write(f"{name}\t{reason}\n")
        print(f"\n  Lista de inválidos guardada en: {out}")
        print("  Primeros inválidos:")
        for name, reason in invalid[:15]:
            print(f"    - {name}: {reason}")
    else:
        print("  Todos los equipos son LEGALES para el formato. ")
    print("-------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida equipos de una carpeta contra el servidor local."
    )
    parser.add_argument(
        "--folder", type=str, default="teams/vgc/reg_i",
        help="Carpeta con los .txt de equipos (default: teams/vgc/reg_i)"
    )
    parser.add_argument(
        "--format", type=str, default="gen9vgc2026regi", dest="battle_format",
        help="Formato a validar (default: gen9vgc2026regi)"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--timeout", type=float, default=25.0,
        help="Segundos max. por equipo antes de marcarlo inválido (default: 25)"
    )
    parser.add_argument(
        "--max", type=int, default=None, dest="max_teams",
        help="Probar solo los primeros N equipos (para una prueba rápida)"
    )
    args = parser.parse_args()

    asyncio.run(check_teams(
        args.folder, args.battle_format, args.port, args.timeout, args.max_teams
    ))
