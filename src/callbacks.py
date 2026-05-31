# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Callbacks de entrenamiento para registrar métricas en TensorBoard.
"""

from collections import deque

from stable_baselines3.common.callbacks import BaseCallback


class WinRateCallback(BaseCallback):
    """
    Registra en TensorBoard la TASA DE VICTORIAS móvil (eval/win_rate) sobre las
    últimas 'window' batallas terminadas.

    La victoria/derrota se deduce de la RECOMPENSA terminal:
      +1 -> victoria, -1 -> derrota, ~0 -> combate abandonado (no cuenta).
    Así es robusto incluso si el entorno se reconstruye (no depende de los
    contadores internos del agente, que se reinician al reconstruir).

    :param log_freq: cada cuántos steps se registra el winrate (0 = nunca).
    :param window: número de batallas recientes sobre las que se promedia.
    """

    def __init__(self, log_freq: int = 5000, window: int = 200):
        super().__init__()
        self.log_freq = log_freq
        self._results: deque[float] = deque(maxlen=window)

    def _on_step(self) -> bool:
        dones = self.locals.get("dones")
        rewards = self.locals.get("rewards")
        if dones is not None and rewards is not None:
            for done, reward in zip(dones, rewards):
                if done:
                    if reward > 0.5:
                        self._results.append(1.0)
                    elif reward < -0.5:
                        self._results.append(0.0)
                    # reward ~0 -> combate abandonado/empate: no se cuenta
        if self.log_freq and self.n_calls % self.log_freq == 0 and self._results:
            self.logger.record(
                "eval/win_rate", sum(self._results) / len(self._results)
            )
            self.logger.record("eval/battles_contadas", len(self._results))
        return True
