# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Entrenamiento del bot dobles con PPO.

FORMATOS SOPORTADOS:
  gen9randomdoublesbattle  -> equipos aleatorios, sin --team
  gen9vgc2025regg          -> VGC con equipo propio, necesita --team

Uso rápido (sin equipo, siempre funciona):
    python train_doubles.py

Uso VGC con equipo:
    python train_doubles.py --team teams/vgc/equipo_ejemplo.txt --format gen9vgc2025regg --total_steps 500000

Requisitos:
    - Servidor pokemon-showdown corriendo: node pokemon-showdown start --no-security
    - Para VGC: fichero de equipo válido en formato Showdown
    - poke-env >= 0.15.0, stable_baselines3 >= 2.7.1

El modelo se guarda en models/doubles/ cada 'save_interval' pasos.
Los logs de TensorBoard se guardan en logs/doubles/.

Nota sobre el espacio de acciones:
    MultiDiscrete([107, 107]) - una acción por cada pokemon activo.
    SB3 PPO lo maneja nativamente con MlpPolicy.
"""

import argparse
import os
import random
from pathlib import Path

import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback

from src.doubles_env import DoublesGymEnv


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def checkpoint_steps(path) -> int | None:
    """
    Extrae el número de pasos del nombre de un checkpoint.
    Devuelve None para ficheros sin número (por ejemplo 'final.zip').
    Ejemplos: 'model_20000_steps' -> 20000 ; 'final' -> None
    """
    stem = path.stem
    cleaned = stem.replace("model_", "").replace("_steps", "")
    try:
        return int(cleaned)
    except ValueError:
        return None


def load_team(team_path: str | None) -> str | None:
    """Carga un equipo desde fichero de texto en formato Showdown."""
    if team_path is None:
        return None
    path = Path(team_path)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el fichero de equipo: {team_path}\n"
            "Crea un equipo en https://play.pokemonshowdown.com/teambuilder\n"
            "y guárdalo en la carpeta teams/vgc/"
        )
    return path.read_text(encoding="utf-8")


def check_server(port: int):
    """Verifica que el servidor Showdown está corriendo en el puerto indicado."""
    import socket
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect(("localhost", port))
        s.close()
    except (ConnectionRefusedError, TimeoutError, OSError):
        raise RuntimeError(
            f"\n ERROR: No hay servidor Showdown en localhost:{port}\n"
            f" Arranca el servidor con:\n"
            f"   cd pokemon-showdown\n"
            f"   node pokemon-showdown start --no-security\n"
        )


def train(
    run_id: int,
    port: int,
    device: str,
    battle_format: str,
    team_path: str | None,
    total_steps: int,
    save_interval: int,
    opponent_type: str = "random",
    policy: str = "mlp",
    tag: str = "",
):
    set_seed(run_id)
    check_server(port)

    # Validar compatibilidad formato <-> equipo
    needs_team = "random" not in battle_format
    if needs_team and team_path is None:
        raise ValueError(
            f"El formato '{battle_format}' requiere un equipo.\n"
            f"  Un equipo fijo:      --team teams/vgc/equipo_ejemplo.txt\n"
            f"  Equipos variados:    --team teams/vgc   (carpeta con varios .txt)\n"
            f"  O usa formato aleatorio: --format gen9randomdoublesbattle"
        )
    if not needs_team and team_path is not None:
        print(f"Nota: --team ignorado para formato de batalla aleatorio '{battle_format}'")
        team_path = None

    if team_path is not None and Path(team_path).is_dir():
        n_teams = len(list(Path(team_path).glob("*.txt")))
        print(f"Usando {n_teams} equipos de '{team_path}' (aleatorio por combate)")

    # Separar modelos por formato Y por política (para comparar mlp vs transformer)
    # 'tag' permite diferenciar modelos/runs (p.ej. tag="selfplay") sin mezclarlos
    # con el mismo seed entrenado contra otro oponente.
    seed_dir = f"seed{run_id}" + (f"_{tag}" if tag else "")
    save_dir = Path("models/doubles") / battle_format / policy / seed_dir
    log_dir = Path("logs/doubles") / battle_format / policy
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creando entorno doubles {battle_format} contra {opponent_type} (policy={policy})...")
    # DoublesGymEnv crea su propio oponente (sin conexión al servidor)
    env = DoublesGymEnv(
        port=port,
        battle_format=battle_format,
        log_level=40,
        team_path=team_path,
        opponent_type=opponent_type,
    )
    print(f"Espacio de acción: {env.action_space}")
    print(f"Espacio de observación: {env.observation_space}")

    # Reanudar desde checkpoint si existe. Probamos de MAYOR a menor número de
    # pasos y cargamos el primero compatible. Así se ignoran automáticamente los
    # checkpoints antiguos de PPO sin action masking (no son cargables por
    # MaskablePPO -> "Policy must subclass MaskableActorCriticPolicy").
    num_saved = 0
    model = None
    numbered = sorted(
        [
            (p, checkpoint_steps(p))
            for p in save_dir.glob("*.zip")
            if checkpoint_steps(p) is not None
        ],
        key=lambda t: t[1],
        reverse=True,
    )
    for cand, steps in numbered:
        try:
            model = MaskablePPO.load(str(cand), env=env, device=device)
            model.num_timesteps = steps
            num_saved = steps
            print(f"Reanudando desde {cand} ({steps} pasos)")
            break
        except Exception as e:
            print(f"AVISO: {cand.name} no es compatible ({type(e).__name__}); "
                  "probando un checkpoint anterior...")
            model = None

    if model is None:
        from src.policy import make_policy_kwargs
        print(f"Creando nuevo modelo MaskablePPO (policy={policy}, action masking)...")
        model = MaskablePPO(
            "MlpPolicy",
            env,
            learning_rate=lambda p: 3e-4 * p,
            n_steps=2048,
            batch_size=256,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            policy_kwargs=make_policy_kwargs(policy),
            verbose=1,
            tensorboard_log=str(log_dir),
            device=device,
        )

    # SELF-PLAY: el rival juega con la propia política que se está entrenando.
    if opponent_type == "self":
        env.set_opponent_model(model)
        print("SELF-PLAY activado: el rival usa la política actual del agente.")

    from src.callbacks import WinRateCallback
    checkpoint_cb = CheckpointCallback(
        save_freq=save_interval,
        save_path=str(save_dir),
        name_prefix="model",
        verbose=1,
    )
    # Registra eval/win_rate en TensorBoard (winrate móvil de las últimas batallas)
    winrate_cb = WinRateCallback(log_freq=5000, window=200)

    remaining = total_steps - num_saved
    if remaining <= 0:
        print(f"Ya se han completado {num_saved} >= {total_steps} pasos.")
    else:
        print(f"Entrenando {remaining} pasos...")
        model.learn(
            total_timesteps=remaining,
            callback=[checkpoint_cb, winrate_cb],
            reset_num_timesteps=False,
            tb_log_name=f"doubles_seed{run_id}" + (f"_{tag}" if tag else ""),
        )
        final_path = save_dir / "final"
        model.save(str(final_path))
        print(f"Modelo final guardado en {final_path}.zip")

    env.close()
    print("Entrenamiento completado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Entrena un bot de dobles VGC con PPO."
    )
    parser.add_argument(
        "--team", type=str, default=None,
        dest="team_path",
        help="Equipo VGC: un fichero .txt (equipo fijo) o una carpeta con "
             "varios .txt (equipo aleatorio en cada combate). "
             "Ej.: teams/vgc/equipo1.txt  o  teams/vgc"
    )
    parser.add_argument(
        "--run_id", type=int, default=1,
        help="Semilla y ID del experimento (default: 1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Puerto del servidor Showdown (default: 8000)"
    )
    parser.add_argument(
        "--device", type=str, default="cpu",
        help="Dispositivo torch: 'cpu' o 'cuda:0' (default: cpu)"
    )
    parser.add_argument(
        "--format", type=str, default="gen9randomdoublesbattle",
        dest="battle_format",
        help="Formato de batalla (default: gen9randomdoublesbattle). "
             "Para VGC usa gen9vgc2025regg con --team."
    )
    parser.add_argument(
        "--total_steps", type=int, default=200_000,
        help="Pasos de entrenamiento totales (default: 200000)"
    )
    parser.add_argument(
        "--save_interval", type=int, default=20_000,
        help="Guardar checkpoint cada N pasos (default: 20000)"
    )
    parser.add_argument(
        "--opponent", type=str, default="random",
        choices=["random", "maxpower", "heuristic", "self"],
        help="Oponente de entrenamiento (default: random). "
             "'maxpower' = MaxBasePowerPlayer (elige el movimiento de mayor potencia); "
             "'heuristic' = SimpleHeuristicsPlayer; "
             "'self' = SELF-PLAY (el rival usa la política actual del agente)."
    )
    parser.add_argument(
        "--policy", type=str, default="mlp",
        choices=["mlp", "transformer"],
        help="Arquitectura de la red (default: mlp). 'transformer' usa un "
             "extractor con atención sobre tokens."
    )
    parser.add_argument(
        "--tag", type=str, default="",
        help="Sufijo para diferenciar el modelo y su run de TensorBoard "
             "(por ejemplo --tag selfplay -> carpeta seed<run_id>_selfplay). "
             "Útil para no mezclar el self-play con el modelo de calentamiento."
    )
    args = parser.parse_args()

    train(
        run_id=args.run_id,
        port=args.port,
        device=args.device,
        battle_format=args.battle_format,
        team_path=args.team_path,
        total_steps=args.total_steps,
        save_interval=args.save_interval,
        opponent_type=args.opponent,
        policy=args.policy,
        tag=args.tag,
    )
