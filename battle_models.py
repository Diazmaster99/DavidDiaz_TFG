# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Enfrenta dos agentes entre sí en el servidor local y reporta el resultado.

Cada lado (--a y --b) puede ser:
  - Un modelo entrenado:  mlp | transformer
  - Un baseline de poke-env:  random | maxpower | heuristic

Se puede medir, por ejemplo:
  - MLP vs Transformer
  - tu modelo vs RandomPlayer / MaxBasePowerPlayer / SimpleHeuristicsPlayer
  - dos seeds del mismo tipo

Los agentes RL usan la misma observación (src/features.py), por lo que
arquitecturas distintas pueden enfrentarse sin problema.

Uso (dobles VGC, tu MLP vs el heurístico de poke-env):
    python battle_models.py --mode doubles --format gen9vgc2026regi \\
        --team teams/vgc/I1.txt --a mlp --b heuristic -n 50

Uso (singles, transformer vs MaxDamage):
    python battle_models.py --mode singles --a transformer --b maxpower -n 50

Requiere el servidor local corriendo:
    node pokemon-showdown start --no-security
"""

import argparse
import asyncio
import socket
from pathlib import Path

from poke_env import AccountConfiguration
from poke_env.player import MaxBasePowerPlayer, RandomPlayer, SimpleHeuristicsPlayer
from sb3_contrib import MaskablePPO

# Reutilizamos los jugadores RL y utilidades de play.py
from play import (
    RLDoublesPlayer,
    RLSinglesPlayer,
    find_latest_model,
    make_server_config,
)
from src.policy import BattleTransformerExtractor  # noqa: F401 (para deserializar)
from src.teams import build_teambuilder

RL_SPECS = ("mlp", "transformer")
BASELINE_CLS = {
    "random": RandomPlayer,
    "maxpower": MaxBasePowerPlayer,
    "heuristic": SimpleHeuristicsPlayer,
}
AGENT_CHOICES = list(RL_SPECS) + list(BASELINE_CLS)


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


def load_model(mode: str, battle_format: str, policy: str, run_id: int, tag: str = ""):
    seed_dir = f"seed{run_id}" + (f"_{tag}" if tag else "")
    model_dir = Path(f"models/{mode}") / battle_format / policy / seed_dir
    path = find_latest_model(model_dir)
    if path is None:
        raise FileNotFoundError(
            f"No se encontró modelo en {model_dir}\n"
            f"Entrena con: python train_{mode}.py --format {battle_format} "
            f"--policy {policy}" + (f" --tag {tag}" if tag else "")
        )
    return MaskablePPO.load(str(path)), path


def make_agent(spec, mode, battle_format, team_builder, server, run_id, name, tag=""):
    """Crea un jugador: modelo RL (mlp/transformer) o baseline de poke-env."""
    common = dict(
        battle_format=battle_format,
        server_configuration=server,
        log_level=40,
        max_concurrent_battles=1,
        account_configuration=AccountConfiguration(name, None),
    )
    if mode == "doubles":
        common["team"] = team_builder

    if spec in RL_SPECS:
        model, path = load_model(mode, battle_format, spec, run_id, tag)
        cls = RLDoublesPlayer if mode == "doubles" else RLSinglesPlayer
        suffix = f"_{tag}" if tag else ""
        return cls(model=model, **common), f"{spec} (seed{run_id}{suffix})"

    base_cls = BASELINE_CLS[spec]
    return base_cls(**common), f"baseline:{spec}"


async def battle(
    mode: str,
    battle_format: str,
    team_path: str | None,
    spec_a: str,
    spec_b: str,
    run_id_a: int,
    run_id_b: int,
    n_battles: int,
    port: int,
    tag_a: str = "",
    tag_b: str = "",
):
    check_server(port)
    server = make_server_config(port, official=False)
    team_builder = build_teambuilder(team_path) if mode == "doubles" else None

    name_a = f"A_{spec_a}_{run_id_a}{('_'+tag_a) if tag_a else ''}"[:18]
    name_b = f"B_{spec_b}_{run_id_b}{('_'+tag_b) if tag_b else ''}"[:18]
    player_a, desc_a = make_agent(
        spec_a, mode, battle_format, team_builder, server, run_id_a, name_a, tag_a
    )
    player_b, desc_b = make_agent(
        spec_b, mode, battle_format, team_builder, server, run_id_b, name_b, tag_b
    )
    print(f"A = {desc_a}")
    print(f"B = {desc_b}")

    # Silenciar el aviso inofensivo de open team sheets en dobles VGC
    if mode == "doubles":
        from src.doubles_env import _SuppressOpenTeamSheetFilter
        f = _SuppressOpenTeamSheetFilter()
        player_a.logger.addFilter(f)
        player_b.logger.addFilter(f)

    print(f"\nEnfrentando {n_battles} combates: A({spec_a}) vs B({spec_b})...")
    await player_a.battle_against(player_b, n_battles=n_battles)

    wins_a = player_a.n_won_battles
    wins_b = player_b.n_won_battles
    ties = player_a.n_tied_battles
    print("\n=================== RESULTADO ===================")
    print(f"  A ({spec_a}):  {wins_a} victorias")
    print(f"  B ({spec_b}):  {wins_b} victorias")
    print(f"  Empates:       {ties}")
    print(f"  Winrate A: {player_a.win_rate:.1%}")
    print("=================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enfrenta dos agentes (modelos RL y/o baselines de poke-env)."
    )
    parser.add_argument("--mode", choices=["singles", "doubles"], required=True)
    parser.add_argument(
        "--format", type=str, default=None, dest="battle_format",
        help="Formato (default: gen9randombattle singles / gen9vgc2026regi doubles)"
    )
    parser.add_argument(
        "--team", type=str, default=None, dest="team_path",
        help="Equipo para dobles VGC (fichero .txt o carpeta)"
    )
    parser.add_argument(
        "--a", type=str, default="mlp", choices=AGENT_CHOICES, dest="spec_a",
        help="Agente A: mlp | transformer | random | maxpower | heuristic"
    )
    parser.add_argument(
        "--b", type=str, default="heuristic", choices=AGENT_CHOICES, dest="spec_b",
        help="Agente B: mlp | transformer | random | maxpower | heuristic"
    )
    parser.add_argument("--run_id_a", type=int, default=1, help="seed del modelo A (si es RL)")
    parser.add_argument("--run_id_b", type=int, default=1, help="seed del modelo B (si es RL)")
    parser.add_argument(
        "--tag_a", type=str, default="",
        help="Sufijo del modelo A (p.ej. selfplay para cargar seed<N>_selfplay)."
    )
    parser.add_argument(
        "--tag_b", type=str, default="",
        help="Sufijo del modelo B (p.ej. selfplay para cargar seed<N>_selfplay)."
    )
    parser.add_argument("-n", type=int, default=20, help="Número de combates")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    fmt = args.battle_format or (
        "gen9vgc2026regi" if args.mode == "doubles" else "gen9randombattle"
    )
    asyncio.run(battle(
        args.mode, fmt, args.team_path,
        args.spec_a, args.spec_b, args.run_id_a, args.run_id_b,
        args.n, args.port, args.tag_a, args.tag_b,
    ))
