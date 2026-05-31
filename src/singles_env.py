# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Entorno Gymnasium para batallas de singles (1v1).

Subclase de poke-env SinglesEnv que implementa:
  - embed_battle: observación detallada (ver src/features.py)
  - calc_reward: recompensa escasa +1/-1 mas bonus por HP

Envuelto en SinglesGymEnv para hacerlo compatible con SB3.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from gymnasium import Env, spaces
from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.battle import Battle
from poke_env.environment.singles_env import SinglesEnv
from poke_env.player.player import Player

from src import poke_env_patch  # noqa: F401  (parche Behemoth Blade/Bash; se aplica al importar)
from src.features import SINGLES_OBS_SIZE, build_singles_obs

# Alias público (lo usa play.py) hacia el embedding detallado de features.py
embed_singles_battle = build_singles_obs


class MySinglesEnv(SinglesEnv):
    """Entorno singles con embedding propio y función de recompensa."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raw_obs = spaces.Box(
            low=np.float32(-10.0),
            high=np.float32(10.0),
            shape=(SINGLES_OBS_SIZE,),
            dtype=np.float32,
        )
        self.observation_spaces = {
            agent: raw_obs for agent in self.possible_agents
        }

    # ------------------------------------------------------------------
    # Metodos abstractos requeridos por PokeEnv
    # ------------------------------------------------------------------

    def embed_battle(self, battle: AbstractBattle) -> npt.NDArray[np.float32]:
        assert isinstance(battle, Battle)
        return embed_singles_battle(battle)

    def calc_reward(self, battle: AbstractBattle) -> float:
        """
        Recompensa:
          +1.0 al ganar, -1.0 al perder.
          Pequenio bonus intermedio basado en HP relativo.
        """
        assert isinstance(battle, Battle)
        if battle.finished:
            return 1.0 if battle.won else -1.0

        # Recompensa intermedia: diferencia de HP para dar gradiente
        own_hp = sum(
            m.current_hp_fraction for m in battle.team.values()
        ) / max(len(battle.team), 1)
        opp_hp = sum(
            m.current_hp_fraction for m in battle.opponent_team.values()
        ) / max(len(battle.opponent_team), 1)
        return (own_hp - opp_hp) * 0.01


class SinglesGymEnv(Env):
    """
    Envoltorio Gymnasium sobre SingleAgentWrapper + MySinglesEnv.

    Aplana la observación (quita el action_mask) para compatibilidad
    con SB3 PPO + MlpPolicy estándar.

    Uso:
        env = SinglesGymEnv(port=8000, battle_format="gen9randombattle")
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        port: int = 8000,
        battle_format: str = "gen9randombattle",
        log_level: int = 40,
        opponent: Player | None = None,
        opponent_type: str = "random",   # "random" o "heuristic"
    ):
        from poke_env.player import MaxBasePowerPlayer, RandomPlayer, SimpleHeuristicsPlayer
        from poke_env.ps_client.server_configuration import ServerConfiguration

        from src.rl_wrapper import OpponentSamplingEnv

        server_cfg = ServerConfiguration(
            f"ws://localhost:{port}/showdown/websocket",
            "https://play.pokemonshowdown.com/action.php?",
        )

        # Factoria: crea un MySinglesEnv listo. El wrapper la usa para crear el
        # entorno y para RECONSTRUIRLO (nueva conexión) si se rompe.
        def _make_poke_env():
            return MySinglesEnv(
                battle_format=battle_format,
                server_configuration=server_cfg,
                log_level=log_level,
                strict=False,        # acciones ilegales -> movimiento aleatorio
                choose_on_teampreview=False,
                start_timer_on_battle_start=True,
                # Baja el timeout del desafío (defecto 60s) para reconstruir el
                # entorno rápido si "Agent is not challenging".
                challenge_timeout=25.0,
            )

        # Oponente: "heuristic" -> SimpleHeuristicsPlayer;
        # "maxpower" -> MaxBasePowerPlayer (movimiento de más potencia);
        # "random" -> None (muestreo de máscara);
        # "self" -> se asigna con set_opponent_model().
        if opponent is None and opponent_type == "heuristic":
            opponent = SimpleHeuristicsPlayer(
                battle_format=battle_format,
                start_listening=False,
            )
        elif opponent is None and opponent_type == "maxpower":
            opponent = MaxBasePowerPlayer(
                battle_format=battle_format,
                start_listening=False,
            )
        self._opponent = opponent

        # OpponentSamplingEnv: evita el bug de order_to_action de poke-env y
        # aporta recuperacion robusta (watchdog + reconstrucción del entorno).
        self._inner = OpponentSamplingEnv(_make_poke_env, opponent=self._opponent)

        self.observation_space = self._inner.observation_space
        self.action_space = self._inner.action_space

    def reset(self, *, seed=None, options=None):
        return self._inner.reset(seed=seed, options=options)

    def step(self, action):
        return self._inner.step(action)

    def action_masks(self):
        """Mascara de acciones legales para MaskablePPO."""
        return self._inner.action_masks()

    def set_opponent_model(self, model):
        """Activa self-play: el rival jugara con la política de 'model'."""
        self._inner.set_opponent_model(model)

    def render(self):
        return self._inner.render()

    def close(self):
        self._inner.close()

    @property
    def win_rate(self) -> float:
        """Tasa de victorias del agente (para monitoreo)."""
        agent = self._inner.poke_env.agent1
        total = agent.n_finished_battles
        return agent.n_won_battles / total if total > 0 else 0.0
