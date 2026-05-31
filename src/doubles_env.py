# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Entorno Gymnasium para batallas de dobles VGC (2v2).

Subclase de poke-env DoublesEnv que implementa:
  - embed_battle: observación detallada (ver src/features.py)
  - calc_reward: recompensa +1/-1 con bonus de HP

Envuelto en DoublesGymEnv para compatibilidad con SB3.

Nota: El espacio de acciones es MultiDiscrete([107, 107]) - una acción por
cada pokemon activo. SB3 PPO soporta MultiDiscrete de forma nativa.
"""

from __future__ import annotations

import logging

import numpy as np
import numpy.typing as npt
from gymnasium import Env, spaces
from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.double_battle import DoubleBattle
from poke_env.environment.doubles_env import DoublesEnv
from poke_env.player.player import Player

from src import poke_env_patch  # noqa: F401  (parche Behemoth Blade/Bash; se aplica al importar)
from src.features import DOUBLES_OBS_SIZE, build_doubles_obs

# Alias público (lo usa play.py) hacia el embedding detallado de features.py
embed_doubles_battle = build_doubles_obs


class _SuppressOpenTeamSheetFilter(logging.Filter):
    """
    Descarta el mensaje CRITICAL inofensivo de poke-env:
      "This format does not allow requesting open team sheets."

    poke-env envia automáticamente /rejectopenteamsheets en cualquier formato
    VGC no-Bo3, pero algunos formatos (p.ej. gen9vgc2026regi no-Bo3) no permiten
    esa peticion y el servidor la rechaza. La batalla continua sin problemas;
    solo silenciamos el ruido en el log.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "open team sheets" not in record.getMessage().lower()


class MyDoublesEnv(DoublesEnv):
    """Entorno dobles con embedding propio y función de recompensa."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raw_obs = spaces.Box(
            low=np.float32(-10.0),
            high=np.float32(10.0),
            shape=(DOUBLES_OBS_SIZE,),
            dtype=np.float32,
        )
        self.observation_spaces = {
            agent: raw_obs for agent in self.possible_agents
        }

    # ------------------------------------------------------------------
    # Metodos abstractos requeridos por PokeEnv
    # ------------------------------------------------------------------

    def embed_battle(self, battle: AbstractBattle) -> npt.NDArray[np.float32]:
        assert isinstance(battle, DoubleBattle)
        return embed_doubles_battle(battle)

    def calc_reward(self, battle: AbstractBattle) -> float:
        """
        Recompensa:
          +1.0 al ganar, -1.0 al perder.
          Pequenio bonus de HP intermedio.
        """
        assert isinstance(battle, DoubleBattle)
        if battle.finished:
            return 1.0 if battle.won else -1.0

        # Bonus intermedio basado en ventaja de HP
        own_hp = sum(
            m.current_hp_fraction for m in battle.team.values()
        ) / max(len(battle.team), 1)
        opp_hp = sum(
            m.current_hp_fraction for m in battle.opponent_team.values()
        ) / max(len(battle.opponent_team), 1)
        return (own_hp - opp_hp) * 0.01


class DoublesGymEnv(Env):
    """
    Envoltorio Gymnasium sobre SingleAgentWrapper + MyDoublesEnv.

    Aplana la observación (quita el action_mask) para compatibilidad
    con SB3 PPO + MlpPolicy.

    El espacio de acciones es MultiDiscrete([107, 107]).
    SB3 maneja MultiDiscrete nativamente con la política "MlpPolicy".

    Formatos soportados:
      - "gen9randomdoublesbattle"  → equipos aleatorios, sin team_path, SIEMPRE funciona.
      - "gen9vgc2025regg" (u otro VGC)  → requiere team_path con equipo VGC válido.

    team_path puede ser:
      - None        → formatos aleatorios (sin equipo)
      - un .txt     → siempre el mismo equipo (mirror match fijo)
      - una carpeta → equipo ALEATORIO por combate (cada batalla usa equipos
                      distintos de tu lista; normalmente no-mirror)

    Uso rápido (sin equipo):
        env = DoublesGymEnv(port=8000)

    Uso VGC con un equipo fijo:
        env = DoublesGymEnv(port=8000, battle_format="gen9vgc2025regg",
                            team_path="teams/vgc/equipo1.txt")

    Uso VGC con equipos variados (carpeta):
        env = DoublesGymEnv(port=8000, battle_format="gen9vgc2025regg",
                            team_path="teams/vgc")

    NOTA: gen9doublesou y similares no funcionan (poke-env solo soporta
    teampreview para formatos VGC en SingleAgentWrapper).
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        port: int = 8000,
        battle_format: str = "gen9randomdoublesbattle",
        log_level: int = 40,
        team_path: str | None = None,
        opponent: Player | None = None,
        opponent_type: str = "random",   # "random" o "heuristic"
    ):
        from poke_env.player import MaxBasePowerPlayer, SimpleHeuristicsPlayer
        from poke_env.ps_client.server_configuration import ServerConfiguration

        from src.rl_wrapper import OpponentSamplingEnv
        from src.teams import build_teambuilder

        server_cfg = ServerConfiguration(
            f"ws://localhost:{port}/showdown/websocket",
            "https://play.pokemonshowdown.com/action.php?",
        )

        # team_path puede ser:
        #   - un fichero .txt -> siempre el mismo equipo (ConstantTeambuilder)
        #   - una carpeta     -> equipo aleatorio por combate (RandomTeamBuilder)
        # Como los 2 agentes comparten el teambuilder, con una carpeta cada lado
        # coge un equipo aleatorio distinto en cada batalla (no-mirror, variado).
        team_builder = build_teambuilder(team_path)

        # Factoria: crea un MyDoublesEnv listo. El wrapper la usa para crear el
        # entorno y para RECONSTRUIRLO (nueva conexión/agentes) si se rompe.
        def _make_poke_env():
            pe = MyDoublesEnv(
                battle_format=battle_format,
                server_configuration=server_cfg,
                log_level=log_level,
                team=team_builder,
                strict=False,        # acciones ilegales -> movimiento aleatorio
                choose_on_teampreview=False,
                # Temporizador del servidor como backstop ante cuelgues.
                start_timer_on_battle_start=True,
                # Si el nuevo desafío no se establece en este tiempo, poke-env
                # lanza "Agent is not challenging". En localhost un desafío bueno
                # tarda <1s; bajamos el defecto (60s) a 25s para que el wrapper
                # detecte el fallo y reconstruya el entorno mucho más rápido.
                challenge_timeout=25.0,
            )
            # Silenciar el CRITICAL inofensivo de open team sheets
            ots = _SuppressOpenTeamSheetFilter()
            pe.agent1.logger.addFilter(ots)
            pe.agent2.logger.addFilter(ots)
            return pe

        # Oponente: "heuristic" -> SimpleHeuristicsPlayer (soporta dobles, sin
        # conexión). "maxpower" -> MaxBasePowerPlayer (movimiento de más potencia).
        # "random" -> None (muestreo de máscara). "self" -> se asigna el modelo
        # después con set_opponent_model().
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

        # OpponentSamplingEnv reemplaza a SingleAgentWrapper (evita el bug de
        # order_to_action de poke-env) y aporta recuperacion robusta (watchdog
        # en step + reconstrucción del entorno si la conexión se rompe).
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
        """Tasa de victorias del agente."""
        agent = self._inner.poke_env.agent1
        total = agent.n_finished_battles
        return agent.n_won_battles / total if total > 0 else 0.0
