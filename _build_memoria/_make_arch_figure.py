# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Genera el diagrama de la arquitectura del sistema para el TFG.
Cuatro capas apiladas (servidor -> poke-env -> wrapper -> SB3/PPO) con
flujo bajada=accion y subida=observacion/recompensa."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

# Capas (de abajo a arriba)
layers = [
    {"y": 0.8, "title": "Servidor Pokémon Showdown (Node.js, fork de vgc-bench)",
     "sub": "Simulación del combate · WebSocket en localhost:8000",
     "color": "#FFCDD2", "edge": "#C62828"},
    {"y": 2.6, "title": "poke-env",
     "sub": "Cliente WebSocket · Interfaz Gymnasium (reset / step)",
     "color": "#FFE0B2", "edge": "#E65100"},
    {"y": 4.4, "title": "Envoltorio de un solo agente (propio)",
     "sub": "Construye la observación detallada y la máscara de acciones legales",
     "color": "#C8E6C9", "edge": "#2E7D32"},
    {"y": 6.2, "title": "Stable-Baselines3  /  MaskablePPO (PyTorch)",
     "sub": "Política + crítico · arquitectura MLP o Transformer",
     "color": "#BBDEFB", "edge": "#1565C0"},
]

BOX_W, BOX_H = 8.4, 1.55
BOX_X = (10 - BOX_W) / 2

for layer in layers:
    box = FancyBboxPatch((BOX_X, layer["y"]), BOX_W, BOX_H,
                          boxstyle="round,pad=0.08,rounding_size=0.18",
                          linewidth=2.0, edgecolor=layer["edge"],
                          facecolor=layer["color"])
    ax.add_patch(box)
    ax.text(5.0, layer["y"] + BOX_H * 0.66, layer["title"],
            ha="center", va="center",
            fontsize=15.5, fontweight="bold")
    ax.text(5.0, layer["y"] + BOX_H * 0.28, layer["sub"],
            ha="center", va="center",
            fontsize=13, style="italic", color="#444444")

# Flechas laterales: bajada = accion, subida = observacion + recompensa
ACTION_COLOR = "#C62828"   # rojo
OBS_COLOR    = "#1565C0"   # azul

# Coordenadas de huecos entre cajas
gaps = []
for i in range(len(layers) - 1):
    top_of_lower = layers[i]["y"] + BOX_H
    bot_of_upper = layers[i+1]["y"]
    gaps.append((top_of_lower, bot_of_upper))

# Flecha de ACCION (baja, derecha) - una sola flecha continua de arriba a abajo
ACC_X = BOX_X + BOX_W + 0.55
for top, bot in gaps:
    ax.annotate("",
                xy=(ACC_X, top + 0.05),
                xytext=(ACC_X, bot - 0.05),
                arrowprops=dict(arrowstyle="-|>", color=ACTION_COLOR, lw=2.6,
                                shrinkA=0, shrinkB=0))
ax.text(ACC_X + 0.05, 5.0, "ACCIÓN",
        rotation=-90, ha="left", va="center",
        fontsize=15.5, fontweight="bold", color=ACTION_COLOR)

# Flecha de OBSERVACION + RECOMPENSA (sube, izquierda)
OBS_X = BOX_X - 0.55
for top, bot in gaps:
    ax.annotate("",
                xy=(OBS_X, bot - 0.05),
                xytext=(OBS_X, top + 0.05),
                arrowprops=dict(arrowstyle="-|>", color=OBS_COLOR, lw=2.6,
                                shrinkA=0, shrinkB=0))
ax.text(OBS_X - 0.05, 5.0, "OBSERVACIÓN  +  RECOMPENSA",
        rotation=90, ha="right", va="center",
        fontsize=15.5, fontweight="bold", color=OBS_COLOR)

# Texto inferior describiendo el ciclo por turno
ax.text(5.0, 0.25,
        "Cada paso del bucle de RL = un turno del combate "
        "(observación → acción → ejecución del turno por el servidor → recompensa)",
        ha="center", va="center", fontsize=13, color="#444444", style="italic")

# (Titulo eliminado: en APA 7 va FUERA de la imagen, encima de la figura)

Path("metrics").mkdir(exist_ok=True)
out = "metrics/figura_arquitectura.png"
plt.tight_layout()
plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
plt.close()
print(f"OK -> {out}")
