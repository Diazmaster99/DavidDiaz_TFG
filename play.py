# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Script de juego interactivo para el bot entrenado.

Carga el modelo más reciente y acepta desafíos. Por defecto se conecta al
servidor local (localhost:8000), el mismo donde entrenas. No necesita
login (el flag --no-security del servidor desactiva la autenticación).

Uso (servidor local, recomendado):
    # 1. Arranca el servidor:  node pokemon-showdown start --no-security
    # 2. Lanza el bot para que acepte desafíos:
    python play.py --mode doubles --username MiBot --run_id 1 \\
        --team teams/vgc/equipo_ejemplo.txt
    # 3. Abre http://localhost:8000 en el navegador, elige el formato
    #    correspondiente y desafía a "MiBot".

    # Singles:
    python play.py --mode singles --username MiBot --run_id 1

Uso (servidor OFICIAL play.pokemonshowdown.com, requiere cuenta registrada):
    python play.py --mode singles --username MiBotRegistrado \\
        --password MiClave --official --ladder -n 10
"""

import argparse
import asyncio
from pathlib import Path

import numpy as np
from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import Player
from poke_env.ps_client.server_configuration import ServerConfiguration
from sb3_contrib import MaskablePPO

from src.singles_env import embed_singles_battle
from src.doubles_env import embed_doubles_battle
# Importado para que MaskablePPO.load pueda reconstruir modelos con extractor
# transformer (la clase debe ser importable al deserializar).
from src.policy import BattleTransformerExtractor  # noqa: F401


def make_server_config(port: int, official: bool):
    """Devuelve la configuración de servidor: local (por defecto) u oficial."""
    if official:
        return ShowdownServerConfiguration
    return ServerConfiguration(
        f"ws://localhost:{port}/showdown/websocket",
        "https://play.pokemonshowdown.com/action.php?",
    )


def _safe_mask(raw_mask, length: int, is_doubles: bool) -> np.ndarray:
    """Convierte la máscara de poke-env a bool y garantiza >=1 acción válida por hueco."""
    mask = np.asarray(raw_mask, dtype=bool)
    if mask.shape[0] != length:
        return np.ones(length, dtype=bool)
    if is_doubles:
        half = length // 2
        if not mask[:half].any():
            mask[0] = True
        if not mask[half:].any():
            mask[half] = True
    elif not mask.any():
        mask[0] = True
    return mask


class RLSinglesPlayer(Player):
    """
    Jugador singles que usa un modelo MaskablePPO cargado.
    Convierte el estado de batalla a observación, calcula la máscara de
    acciones legales y elige (determinísticamente) una acción legal.
    """

    def __init__(self, model: MaskablePPO, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def choose_move(self, battle):
        from poke_env.battle.battle import Battle
        from poke_env.environment.singles_env import SinglesEnv
        assert isinstance(battle, Battle)
        obs = embed_singles_battle(battle)
        try:
            mask = _safe_mask(
                SinglesEnv.get_action_mask(battle),
                SinglesEnv.get_action_space_size(battle.gen),
                is_doubles=False,
            )
            action, _ = self._model.predict(
                obs, deterministic=True, action_masks=mask
            )
            order = SinglesEnv.action_to_order(
                np.int64(action), battle, fake=False, strict=False
            )
        except Exception:
            return self.choose_random_move(battle)
        return order

    def teampreview(self, battle):
        return "/team 1234"


class RLDoublesPlayer(Player):
    """Jugador doubles que usa un modelo MaskablePPO cargado."""

    def __init__(self, model: MaskablePPO, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def choose_move(self, battle):
        from poke_env.battle.double_battle import DoubleBattle
        from poke_env.environment.doubles_env import DoublesEnv
        assert isinstance(battle, DoubleBattle)
        obs = embed_doubles_battle(battle)
        try:
            mask = _safe_mask(
                DoublesEnv.get_action_mask(battle),
                2 * DoublesEnv.get_action_space_size(battle.gen),
                is_doubles=True,
            )
            action, _ = self._model.predict(
                obs, deterministic=True, action_masks=mask
            )
            order = DoublesEnv.action_to_order(
                action, battle, fake=False, strict=False
            )
        except Exception:
            return self.choose_random_move(battle)
        return order

    def teampreview(self, battle):
        return "/team 1234"


def find_latest_model(model_dir: Path) -> Path | None:
    """Busca el checkpoint más reciente en un directorio."""
    checkpoints = sorted(
        model_dir.glob("*.zip"),
        key=lambda p: p.stat().st_mtime,
    )
    return checkpoints[-1] if checkpoints else None


async def play_singles(
    username: str,
    password: str | None,
    run_id: int,
    n_games: int,
    play_on_ladder: bool,
    battle_format: str,
    port: int,
    official: bool,
    policy: str = "mlp",
    max_concurrent: int = 1,
    tag: str = "",
):
    seed_dir = f"seed{run_id}" + (f"_{tag}" if tag else "")
    model_dir = Path("models/singles") / battle_format / policy / seed_dir
    model_path = find_latest_model(model_dir)
    if model_path is None:
        print(f"No se encontró ningún modelo en {model_dir}")
        print(f"Entrena primero con: python train_singles.py --format {battle_format} --policy {policy}")
        return

    print(f"Cargando modelo desde {model_path}")
    model = MaskablePPO.load(str(model_path))

    server = "OFICIAL" if official else f"LOCAL (localhost:{port})"
    print(f"Conectando al servidor {server}")
    player = RLSinglesPlayer(
        model=model,
        account_configuration=AccountConfiguration(username, password),
        battle_format=battle_format,
        server_configuration=make_server_config(port, official),
        log_level=20,
        max_concurrent_battles=max_concurrent,
    )

    if play_on_ladder:
        print(f"Entrando en la ladder ({n_games} partidas)...")
        await player.ladder(n_games=n_games)
        print(
            f"Resultado: {player.n_won_battles}W - "
            f"{player.n_lost_battles}L - {player.n_tied_battles}T"
        )
    else:
        print(f"Esperando {n_games} desafíos en {battle_format}...")
        await player.accept_challenges(opponent=None, n_challenges=n_games)
        print(
            f"Resultado: {player.n_won_battles}W - "
            f"{player.n_lost_battles}L - {player.n_tied_battles}T"
        )


async def play_doubles(
    username: str,
    password: str | None,
    run_id: int,
    n_games: int,
    play_on_ladder: bool,
    battle_format: str,
    team_path: str | None,
    port: int,
    official: bool,
    open_team_sheets: bool = False,
    policy: str = "mlp",
    max_concurrent: int = 1,
    tag: str = "",
):
    seed_dir = f"seed{run_id}" + (f"_{tag}" if tag else "")
    model_dir = Path("models/doubles") / battle_format / policy / seed_dir
    model_path = find_latest_model(model_dir)
    if model_path is None:
        print(f"No se encontró ningún modelo en {model_dir}")
        print(f"Entrena primero con: python train_doubles.py --format {battle_format} --policy {policy} --team TU_EQUIPO")
        return

    print(f"Cargando modelo desde {model_path}")
    model = MaskablePPO.load(str(model_path))

    # team_path: fichero .txt (equipo fijo) o carpeta (aleatorio por combate)
    from src.teams import build_teambuilder
    team_builder = build_teambuilder(team_path)

    server = "OFICIAL" if official else f"LOCAL (localhost:{port})"
    print(f"Conectando al servidor {server}")
    if open_team_sheets:
        print("Open Team Sheets ACTIVADAS (solo funciona si el formato lo permite, "
              "por ejemplo formatos Bo3).")
    player = RLDoublesPlayer(
        model=model,
        account_configuration=AccountConfiguration(username, password),
        battle_format=battle_format,
        server_configuration=make_server_config(port, official),
        log_level=20,
        max_concurrent_battles=max_concurrent,
        team=team_builder,
        accept_open_team_sheet=open_team_sheets,
    )

    if play_on_ladder:
        print(f"Entrando en la ladder doubles ({n_games} partidas)...")
        await player.ladder(n_games=n_games)
        print(
            f"Resultado: {player.n_won_battles}W - "
            f"{player.n_lost_battles}L - {player.n_tied_battles}T"
        )
    else:
        print(f"Esperando {n_games} desafíos en {battle_format}...")
        await player.accept_challenges(opponent=None, n_challenges=n_games)
        print(
            f"Resultado: {player.n_won_battles}W - "
            f"{player.n_lost_battles}L - {player.n_tied_battles}T"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Juega con el bot entrenado en Showdown."
    )
    parser.add_argument(
        "--mode", choices=["singles", "doubles"], required=True,
        help="Modo de juego"
    )
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, default=None)
    parser.add_argument("--run_id", type=int, default=1)
    parser.add_argument(
        "--format", type=str, default=None, dest="battle_format",
        help="Formato de batalla (por defecto: gen9randombattle para singles, "
             "gen9vgc2025regg para doubles)"
    )
    parser.add_argument(
        "--team", type=str, default=None, dest="team_path",
        help="Fichero de equipo (requerido para doubles VGC)"
    )
    parser.add_argument("-n", type=int, default=5, help="Número de partidas")
    parser.add_argument(
        "-l", "--ladder", action="store_true",
        help="Jugar en la ladder en vez de aceptar desafíos"
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Puerto del servidor LOCAL (default: 8000)"
    )
    parser.add_argument(
        "--official", action="store_true",
        help="Conectar al servidor OFICIAL play.pokemonshowdown.com "
             "(requiere cuenta registrada y --password). Por defecto usa el local."
    )
    parser.add_argument(
        "--ots", action="store_true",
        help="Aceptar Open Team Sheets en dobles VGC (revela los equipos completos "
             "al inicio). Solo funciona si el formato lo permite (p.ej. formatos Bo3)."
    )
    parser.add_argument(
        "--policy", type=str, default="mlp",
        choices=["mlp", "transformer"],
        help="Arquitectura del modelo a cargar (debe coincidir con el entrenado). "
             "Default: mlp."
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=1, dest="max_concurrent",
        help="Número máximo de combates SIMULTÁNEOS que acepta el bot (default: 1). "
             "Súbelo (p.ej. 3) si quieres que varias personas le reten a la vez y "
             "juegue todos los combates en paralelo desde la misma cuenta."
    )
    parser.add_argument(
        "--tag", type=str, default="",
        help="Sufijo del modelo a cargar (debe coincidir con el del entrenamiento, "
             "p.ej. --tag selfplay para cargar el modelo de seed<N>_selfplay)."
    )
    args = parser.parse_args()

    if args.official and not args.password:
        print("AVISO: el servidor oficial suele requerir --password para nombres registrados.")

    if args.mode == "singles":
        fmt = args.battle_format or "gen9randombattle"
        asyncio.run(play_singles(
            args.username, args.password, args.run_id,
            args.n, args.ladder, fmt, args.port, args.official, args.policy,
            args.max_concurrent, args.tag,
        ))
    else:
        fmt = args.battle_format or "gen9vgc2025regg"
        asyncio.run(play_doubles(
            args.username, args.password, args.run_id,
            args.n, args.ladder, fmt, args.team_path, args.port, args.official,
            args.ots, args.policy, args.max_concurrent, args.tag,
        ))
