# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Extractor de características basado en TRANSFORMER (atención)

En vez de tratar la observación como un vector plano (lo que hace el MLP),
la trocea en TOKENS (una "ficha" por entidad: global, cada Pokémon, cada
movimiento), proyecta cada ficha a una dimensión común y aplica atención para
que las fichas se "miren" entre sí. Un token CLS resume toda la batalla.

Ventajas frente al MLP plano:
  - Un MISMO codificador por tipo de entidad (peso compartido) -> generaliza
    mejor (lo aprendido de un Pokémon sirve para todos).
  - La atención captura relaciones (matchups, sinergias) de forma natural.

Se activa con --policy transformer en los scripts de entrenamiento. El MLP
sigue siendo el valor por defecto (para comparar ambos en la memoria).
"""

from __future__ import annotations

import torch
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from torch import nn

from src.features import (
    DOUBLES_OBS_SIZE,
    SINGLES_OBS_SIZE,
    doubles_token_segments,
    singles_token_segments,
)


class BattleTransformerExtractor(BaseFeaturesExtractor):
    """
    Convierte la observación plana en una secuencia de tokens y aplica un
    TransformerEncoder. Devuelve el embedding del token CLS como vector de
    características (sobre el que SB3 monta las cabezas de política/valor).

    :param embed_dim: dimensión de cada token (d_model del transformer).
    :param nhead: número de cabezas de atención.
    :param num_layers: número de capas del encoder.
    :param dim_ff: dimensión de la capa feed-forward interna.
    """

    def __init__(
        self,
        observation_space: spaces.Box,
        embed_dim: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_ff: int = 128,
    ):
        super().__init__(observation_space, features_dim=embed_dim)
        n = int(observation_space.shape[0])
        if n == SINGLES_OBS_SIZE:
            self._segments = singles_token_segments()
        elif n == DOUBLES_OBS_SIZE:
            self._segments = doubles_token_segments()
        else:
            raise ValueError(
                f"Observación de dim {n} no soportada por el transformer "
                f"(esperado {SINGLES_OBS_SIZE} o {DOUBLES_OBS_SIZE})."
            )

        # Una proyección lineal por TIPO de entidad (peso compartido entre
        # todas las fichas del mismo tipo: todos los Pokémon usan el mismo
        # encoder, todos los movimientos el mismo, etc.).
        lengths: dict[str, int] = {}
        for kind, _, length in self._segments:
            lengths[kind] = length
        self.proj = nn.ModuleDict(
            {kind: nn.Linear(length, embed_dim) for kind, length in lengths.items()}
        )

        # Token CLS aprendible que resumirá toda la batalla.
        self.cls = nn.Parameter(torch.zeros(1, 1, embed_dim))
        nn.init.normal_(self.cls, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=nhead,
            dim_feedforward=dim_ff,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        batch = observations.shape[0]
        tokens = []
        for kind, start, length in self._segments:
            segment = observations[:, start : start + length]   # (B, length)
            tokens.append(self.proj[kind](segment))             # (B, embed_dim)
        x = torch.stack(tokens, dim=1)                          # (B, n_tokens, D)
        cls = self.cls.expand(batch, -1, -1)                    # (B, 1, D)
        x = torch.cat([cls, x], dim=1)                          # (B, 1+n_tokens, D)
        x = self.encoder(x)                                     # (B, 1+n_tokens, D)
        return x[:, 0]                                          # embedding del CLS


def make_policy_kwargs(policy: str) -> dict:
    """
    Devuelve los policy_kwargs para MaskablePPO según la arquitectura elegida.
      'mlp'         -> MLP plano [256, 256] (por defecto)
      'transformer' -> extractor con atención + cabezas [128, 128]
    """
    if policy == "transformer":
        return {
            "features_extractor_class": BattleTransformerExtractor,
            "features_extractor_kwargs": {
                "embed_dim": 64,
                "nhead": 4,
                "num_layers": 2,
                "dim_ff": 128,
            },
            "net_arch": [128, 128],
        }
    return {"net_arch": [256, 256]}
