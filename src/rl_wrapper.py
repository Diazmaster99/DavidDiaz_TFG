# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Wrapper Gymnasium que controla a un agente con RL y al oponente, con
RECUPERACIÓN ROBUSTA ante los cuelgues conocidos de poke-env + servidor local.

Doble función:
  1) Convierte el PokeEnv (PettingZoo, 2 agentes) en un entorno Gymnasium de un
     solo agente. agent1 = política RL; agent2 = oponente (aleatorio válido,
     heurístico, o self-play con una política).
  2) Hace el entrenamiento RESILIENTE:
       - watchdog en step(): si un turno se queda colgado (desincronización
         poke-env/servidor en dobles), lo abandona en 'step_timeout' segundos
         en vez de esperar minutos al temporizador del servidor.
       - reconstrucción del entorno: si reset() o un turno fallan, se cierra la
         conexión rota y se crea un PokeEnv NUEVO (agentes/websocket limpios),
         que es lo único que recupera de un estado de conexión corrupto.

NOTA: el oponente se muestrea de la máscara de acciones (no se usa el
SingleAgentWrapper de poke-env, que tiene un bug en order_to_action de dobles).
"""

from __future__ import annotations

import os
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError

import numpy as np
from gymnasium import Env, spaces

# MODO DEBUG: ponlo a 1 para DESACTIVAR el watchdog y los reintentos/reconstrucción
# y ver el TRACEBACK REAL del error (en vez de tragarselo). Uso:
#   Windows (PowerShell):  $env:POKE_ENV_DEBUG = "1"
#   Windows (cmd):         set POKE_ENV_DEBUG=1
#   Linux/Mac:             export POKE_ENV_DEBUG=1
# Dejalo SIN definir (o a 0) para entrenamientos normales (robustez activada).
DEBUG = os.environ.get("POKE_ENV_DEBUG", "") not in ("", "0", "false", "False")

# Parche de poke-env para los movimientos que cambian de id al cambiar de forma
# (Zacian/Zamazenta-Coronado: Behemoth Blade/Bash). Arregla la conversión
# orden<->acción en AMBOS sentidos (agente y oponente). Se aplica al importarlo.
from src import poke_env_patch  # noqa: E402,F401


class OpponentSamplingEnv(Env):
    metadata = {"render_modes": []}

    def __init__(self, env_factory, opponent=None, step_timeout: float = 30.0):
        """
        :param env_factory: callable SIN argumentos que crea un PokeEnv listo
            (ya configurado, con sus filtros de log). Se usa para crear el
            entorno y para RECONSTRUIRLO si la conexión se rompe.
        :param opponent: Player opcional (p.ej. SimpleHeuristicsPlayer) para
            decidir las jugadas del rival. None -> aleatorio válido (o self-play
            si se asigna un modelo con set_opponent_model()).
        :param step_timeout: segundos máximos para un turno antes de considerar
            el combate atascado y reconstruir el entorno.
        """
        self._factory = env_factory
        self._env = env_factory()
        self._opponent = opponent
        self._opponent_model = None        # SELF-PLAY si se asigna
        self._step_timeout = step_timeout
        self._executor = ThreadPoolExecutor(max_workers=1)

        a1 = self._env.agent1.username
        self.observation_space = self._env.observation_spaces[a1]["observation"]
        self.action_space = self._env.action_spaces[a1]
        self._is_doubles = isinstance(self.action_space, spaces.MultiDiscrete)
        if self._is_doubles:
            self._mask_len = int(self.action_space.nvec.sum())   # 214
        else:
            self._mask_len = int(self.action_space.n)            # 26
        self._last_mask = np.ones(self._mask_len, dtype=bool)

    # ------------------------------------------------------------------

    @property
    def poke_env(self):
        return self._env

    def set_opponent_model(self, model):
        """Activa SELF-PLAY: el rival juega con la política de 'model'."""
        self._opponent_model = model

    # ------------------------------------------------------------------
    # Recuperación

    def _force_finish_battles(self):
        """Marca como terminadas las batallas colgadas en los 2 agentes."""
        pe = self._env
        for agent in (getattr(pe, "agent1", None), getattr(pe, "agent2", None)):
            if agent is None:
                continue
            try:
                for b in list(agent._battles.values()):
                    if not b.finished:
                        b._finished = True
            except Exception:
                pass
        pe.battle1 = None
        pe.battle2 = None

    def _finish_lingering_battles(self):
        """Marca como terminadas las batallas locales que hayan quedado sin
        cerrar (p.ej. tras un turno abortado, o un final no detectado en uno de
        los dos bandos en dobles). Así poke-env puede reiniciar sin lanzar
        'Can not reset player's battles while they are still running', evitando
        la costosa reconstrucción del entorno. No anula battle1/battle2: poke-env
        los reasigna en su propio reset()."""
        pe = self._env
        for agent in (getattr(pe, "agent1", None), getattr(pe, "agent2", None)):
            if agent is None:
                continue
            try:
                for b in list(agent._battles.values()):
                    if not b.finished:
                        b._finished = True
            except Exception:
                pass

    def _rebuild(self):
        """Cierra el entorno roto y crea uno NUEVO (conexión/agentes limpios)."""
        self._force_finish_battles()
        try:
            # IMPORTANTE: wait=False. El close() de poke-env, con su valor por
            # defecto wait=True, hace self._challenge_task.result() SIN timeout;
            # si el desafío está colgado (justo lo que provoca "Agent is not
            # challenging"), ese .result() bloquea PARA SIEMPRE y congela todo el
            # entrenamiento. Con wait=False se descarta la tarea colgada y se crea
            # un entorno nuevo y limpio.
            self._env.close(wait=False)
        except Exception:
            pass
        # El worker del executor puede estar bloqueado en un step colgado:
        # lo abandonamos y creamos uno nuevo.
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self._executor = ThreadPoolExecutor(max_workers=1)
        time.sleep(2)
        self._env = self._factory()

    # ------------------------------------------------------------------

    def reset(self, *, seed=None, options=None):
        attempts = 4
        for i in range(attempts):
            try:
                # Limpieza preventiva: cierra batallas locales sin terminar para
                # evitar el OSError "battles still running" y la reconstrucción
                # del entorno (que es lenta). Es inocua en el reset normal.
                self._finish_lingering_battles()
                obs, infos = self._env.reset(seed, options)
                if self._opponent is not None and self._env.battle2 is not None:
                    self._opponent.reset_battles()
                    self._opponent._battles[
                        self._env.battle2.battle_tag
                    ] = self._env.battle2
                a1 = self._env.agents[0]
                self._last_mask = self._extract_mask(obs[a1])
                return obs[a1]["observation"], infos[a1]
            except (TimeoutError, OSError) as e:
                # TimeoutError ("Agent is not challenging") y OSError ("battles
                # still running") indican conexión/estado roto: reconstruimos.
                if DEBUG:
                    # Modo debug: sin reintentos; muestra el traceback real.
                    print("[env.reset] MODO DEBUG: traceback real ->", flush=True)
                    traceback.print_exc()
                    raise
                if i == attempts - 1:
                    raise
                print(
                    f"[env.reset] fallo ({type(e).__name__}: {e}); reconstruyendo "
                    f"entorno y reintentando ({i + 1}/{attempts - 1})...",
                    flush=True,
                )
                self._rebuild()

    def step(self, action):
        pe = self._env
        b1, b2 = pe.battle1, pe.battle2

        # Guardia: si la batalla ya terminó, estado terminal limpio.
        if (b1 is not None and b1.finished) or (b2 is not None and b2.finished):
            reward = 0.0
            if b1 is not None and b1.finished:
                reward = 1.0 if b1.won else -1.0
            pe.battle1 = None
            pe.battle2 = None
            self._last_mask = np.ones(self._mask_len, dtype=bool)
            return self._zeros(), reward, True, False, {}

        a1, a2 = pe.agents[0], pe.agents[1]
        opp_action = self._opponent_action(b2)
        actions = {a1: action, a2: opp_action}

        # Ejecutar el turno con WATCHDOG: si tarda más de step_timeout, el
        # combate está atascado -> abandonar y reconstruir (rápido, sin esperar
        # al temporizador del servidor, que tarda minutos).
        if DEBUG:
            # Modo debug: sin watchdog ni captura -> traceback real del turno.
            obs, rewards, terms, truncs, infos = pe.step(actions)
        else:
            try:
                fut = self._executor.submit(pe.step, actions)
                obs, rewards, terms, truncs, infos = fut.result(timeout=self._step_timeout)
            except FuturesTimeoutError:
                print(
                    f"[env.step] turno atascado >{self._step_timeout:.0f}s; "
                    f"abandonando combate y reconstruyendo entorno...",
                    flush=True,
                )
                self._rebuild()
                self._last_mask = np.ones(self._mask_len, dtype=bool)
                return self._zeros(), 0.0, True, False, {}
            except (AssertionError, ValueError, IndexError):
                pe.battle1 = None
                pe.battle2 = None
                self._last_mask = np.ones(self._mask_len, dtype=bool)
                return self._zeros(), 0.0, True, False, {}

        a1_obs = obs[a1]
        self._last_mask = self._extract_mask(a1_obs)
        return (
            a1_obs["observation"],
            rewards[a1],
            terms[a1],
            truncs[a1],
            infos[a1],
        )

    # ------------------------------------------------------------------

    def action_masks(self) -> np.ndarray:
        """Máscara de acciones legales del agente RL (la consume MaskablePPO)."""
        return self._last_mask

    def _extract_mask(self, agent_obs) -> np.ndarray:
        return self._sanitize_mask(agent_obs["action_mask"])

    def _sanitize_mask(self, mask) -> np.ndarray:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape[0] != self._mask_len:
            return np.ones(self._mask_len, dtype=bool)
        if self._is_doubles:
            half = self._mask_len // 2
            if not mask[:half].any():
                mask[0] = True
            if not mask[half:].any():
                mask[half] = True
        elif not mask.any():
            mask[0] = True
        return mask

    def _zeros(self) -> np.ndarray:
        return np.zeros(self.observation_space.shape, dtype=np.float32)

    def _opponent_action(self, battle):
        """
        Acción del oponente, por prioridad:
          1. SELF-PLAY (opponent_model) -> política RL.
          2. HEURÍSTICO (Player) -> choose_move.
          3. ALEATORIO -> muestreo de la máscara.
        """
        if self._opponent_model is not None:
            try:
                obs = self._env.embed_battle(battle)
                mask = self._sanitize_mask(self._env.get_action_mask(battle))
                action, _ = self._opponent_model.predict(
                    obs, action_masks=mask, deterministic=False
                )
                action = np.asarray(action)
                if self._is_doubles:
                    return action.reshape(-1)[:2].astype(np.int64)
                return np.int64(action.reshape(-1)[0])
            except Exception:
                if DEBUG:
                    print("[opponent_model] error (se usaría aleatorio) ->", flush=True)
                    traceback.print_exc()

        if self._opponent is not None:
            try:
                from collections.abc import Awaitable
                order = self._opponent.choose_move(battle)
                if not isinstance(order, Awaitable):
                    return self._env.order_to_action(
                        order, battle, fake=False, strict=False
                    )
            except Exception:
                if DEBUG:
                    print("[opponent] error (se usaría aleatorio) ->", flush=True)
                    traceback.print_exc()

        return self._sample_from_mask(battle)

    def _sample_from_mask(self, battle):
        mask = self._env.get_action_mask(battle)
        if self._is_doubles:
            half = len(mask) // 2
            valid0 = [i for i, m in enumerate(mask[:half]) if m] or [0]
            valid1 = [i for i, m in enumerate(mask[half:]) if m] or [0]
            return np.array(
                [random.choice(valid0), random.choice(valid1)], dtype=np.int64
            )
        valid = [i for i, m in enumerate(mask) if m] or [0]
        return np.int64(random.choice(valid))

    def render(self):
        return self._env.render()

    def close(self):
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            # wait=False para no quedar bloqueado en _challenge_task.result()
            # si quedara un desafío colgado al cerrar (ver _rebuild).
            self._env.close(wait=False)
        except Exception:
            pass
