# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Genera los dos diagramas UML 2 que pide el Anexo A:
   1) Diagrama de componentes
   2) Diagrama de clases
Usa PlantUML (lenguaje textual UML 2) y los renderiza llamando al servidor
publico www.plantuml.com (no requiere instalacion local de Java)."""
import zlib
import urllib.request
import urllib.error
import ssl
from pathlib import Path

OUT = Path("metrics")
OUT.mkdir(exist_ok=True)

# ---------- Codificacion de PlantUML (deflate + base64 propio) ----------
def _enc6(b):
    if b < 10: return chr(48 + b)
    b -= 10
    if b < 26: return chr(65 + b)
    b -= 26
    if b < 26: return chr(97 + b)
    b -= 26
    if b == 0: return '-'
    if b == 1: return '_'
    return '?'

def _append3(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return _enc6(c1) + _enc6(c2) + _enc6(c3) + _enc6(c4)

def plantuml_encode(source: str) -> str:
    data = zlib.compress(source.encode("utf-8"))[2:-4]   # quita cabecera zlib y crc
    res = []
    for i in range(0, len(data), 3):
        b1 = data[i]
        b2 = data[i+1] if i+1 < len(data) else 0
        b3 = data[i+2] if i+2 < len(data) else 0
        res.append(_append3(b1, b2, b3))
    return "".join(res)

def render(source: str, out_png: Path):
    enc = plantuml_encode(source)
    url = f"https://www.plantuml.com/plantuml/png/{enc}"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept": "image/png,*/*",
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            png = r.read()
        out_png.write_bytes(png)
        print(f"OK  {out_png}  ({len(png)} bytes)")
    except urllib.error.URLError as e:
        print(f"FALLO al renderizar {out_png.name}: {e}")
        raise

# ====================================================================
#  1) DIAGRAMA DE COMPONENTES
# ====================================================================
COMPONENTS = r"""
@startuml
skinparam componentStyle uml2
skinparam backgroundColor White
skinparam shadowing false
skinparam ArrowColor #555555
skinparam ComponentBackgroundColor<<own>>      #C8E6C9
skinparam ComponentBorderColor<<own>>          #2E7D32
skinparam ComponentBackgroundColor<<external>> #FFE0B2
skinparam ComponentBorderColor<<external>>     #E65100
skinparam ComponentBackgroundColor<<server>>   #FFCDD2
skinparam ComponentBorderColor<<server>>       #C62828
skinparam ComponentBackgroundColor<<rl>>       #BBDEFB
skinparam ComponentBorderColor<<rl>>           #1565C0
skinparam DefaultFontName Arial
skinparam DefaultFontSize 14

' --- Componente del servidor (externo, Node.js) ---
component "Pokémon Showdown\n(Node.js, fork de vgc-bench)" as srv <<server>>

' --- Componentes externos de Python ---
package "Bibliotecas externas (Python)" {
  component "poke-env\n(cliente WebSocket\n+ interfaz Gymnasium)" as pe <<external>>
  component "Stable-Baselines3 +\nsb3-contrib (MaskablePPO)" as sb3 <<rl>>
  component "PyTorch" as pt <<external>>
}

' --- Componentes propios del proyecto ---
package "Código propio del proyecto" {
  component "Parche poke-env\n(Behemoth Blade y Bash)" as patch <<own>>
  component "Entornos del proyecto\nMySinglesEnv / MyDoublesEnv" as envs <<own>>
  component "Envoltorio de un solo agente\n(OpponentSamplingEnv)" as wrap <<own>>
  component "Envoltorios SB3\nSinglesGymEnv / DoublesGymEnv" as sbgym <<own>>
  component "features.py\n(observación detallada)" as feats <<own>>
  component "policy.py\n(MLP / extractor Transformer)" as pol <<own>>
  component "WinRateCallback\n(callbacks.py)" as cb <<own>>
  component "Scripts de entrada\n(train_singles, train_doubles,\nplay, battle_models,\nselfplay_from, plot_metrics)" as scripts <<own>>
}

' --- Relaciones de dependencia ---
scripts ..> sbgym
sbgym ..> wrap
sbgym ..> sb3
sbgym ..> pol
wrap ..> envs
envs ..> pe
envs ..> feats
pol ..> pt
sb3 ..> pt
patch ..> pe : <<parche>>
scripts ..> sb3
sb3 ..> cb
pe ..> srv : WebSocket\n(localhost:8000)

@enduml
"""

# ====================================================================
#  2) DIAGRAMA DE CLASES
# ====================================================================
CLASSES = r"""
@startuml
skinparam classAttributeIconSize 0
skinparam backgroundColor White
skinparam shadowing false
skinparam ArrowColor #555555
skinparam ClassBackgroundColor<<own>>       #C8E6C9
skinparam ClassBorderColor<<own>>           #2E7D32
skinparam ClassBackgroundColor<<external>>  #FFE0B2
skinparam ClassBorderColor<<external>>      #E65100
skinparam DefaultFontName Arial
skinparam DefaultFontSize 12

' --- Clases base externas ---
abstract class "SinglesEnv\n(poke-env)" as SinglesEnv <<external>>
abstract class "DoublesEnv\n(poke-env)" as DoublesEnv <<external>>
abstract class "gymnasium.Env" as GymEnv <<external>>
abstract class "BaseFeaturesExtractor\n(Stable-Baselines3)" as BFE <<external>>
abstract class "BaseCallback\n(Stable-Baselines3)" as BCb <<external>>

' --- Clases propias ---
class MySinglesEnv <<own>> {
  + embed_battle(battle)
  + calc_reward(battle)
}
class MyDoublesEnv <<own>> {
  + embed_battle(battle)
  + calc_reward(battle)
}
class OpponentSamplingEnv <<own>> {
  - env_factory
  - opponent
  - opponent_model
  - step_timeout
  + reset(seed, options)
  + step(action)
  + action_masks()
  + set_opponent_model(model)
  - _finish_lingering_battles()
  - _force_finish_battles()
  - _rebuild()
  - _opponent_action(battle)
}
class SinglesGymEnv <<own>> {
  + reset(seed, options)
  + step(action)
  + action_masks()
  + close()
}
class DoublesGymEnv <<own>> {
  + reset(seed, options)
  + step(action)
  + action_masks()
  + close()
}
class BattleTransformerExtractor <<own>> {
  - d_model
  - n_heads
  - n_layers
  - segments
  + forward(observations)
}
class WinRateCallback <<own>> {
  - log_freq
  - window
  - _results
  + _on_step()
}

' --- Herencias ---
SinglesEnv <|-- MySinglesEnv
DoublesEnv <|-- MyDoublesEnv
GymEnv     <|-- OpponentSamplingEnv
GymEnv     <|-- SinglesGymEnv
GymEnv     <|-- DoublesGymEnv
BFE        <|-- BattleTransformerExtractor
BCb        <|-- WinRateCallback

' --- Asociaciones / composiciones ---
SinglesGymEnv "1" *-- "1" OpponentSamplingEnv : _inner
DoublesGymEnv "1" *-- "1" OpponentSamplingEnv : _inner
OpponentSamplingEnv ..> MySinglesEnv : crea\n(factory)
OpponentSamplingEnv ..> MyDoublesEnv : crea\n(factory)

@enduml
"""

# ---------------- Guardado y render ----------------
(OUT / "uml_componentes.puml").write_text(COMPONENTS, encoding="utf-8")
(OUT / "uml_clases.puml").write_text(CLASSES, encoding="utf-8")
print("Fuentes .puml guardadas en metrics/.")

render(COMPONENTS, OUT / "uml_componentes.png")
render(CLASSES,    OUT / "uml_clases.png")
print("\nListo.")
