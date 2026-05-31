# DavidDiaz_TFG — Agente de aprendizaje por refuerzo para Pokémon VGC

Bot de inteligencia artificial que juega combates Pokémon, con especial atención al formato competitivo oficial de **dobles VGC**. Implementado en Python sobre **Stable-Baselines3** (MaskablePPO), **poke-env** y un servidor local de **Pokémon Showdown**.

Proyecto de Trabajo de Fin de Grado del Grado en Diseño y Desarrollo de Videojuegos (Especialidad de Programación) de la **Universidad de Diseño, Innovación y Tecnología (UDIT)**, curso académico 2025–2026.

> **Autor:** David Díaz Espinosa de los Monteros

---

## Qué hace

- Entrena agentes de aprendizaje por refuerzo (PPO con *action masking* mediante **MaskablePPO**) para combates Pokémon, en formatos **singles** y **dobles VGC**.
- Soporta dos arquitecturas de red comparables: un **perceptrón multicapa (MLP)** y un **extractor basado en atención (Transformer)**.
- Permite cuatro modalidades de oponente durante el entrenamiento:
  - `random` — jugador aleatorio (acciones legales).
  - `maxpower` — siempre el movimiento de mayor potencia base.
  - `heuristic` — `SimpleHeuristicsPlayer` de poke-env (reglas básicas de efectividad y cambio).
  - `self` — *self-play* (el rival usa la política actual del agente).
- Una vez entrenado, el agente puede aceptar desafíos en el simulador local o jugar en la ladder del servidor oficial `play.pokemonshowdown.com` (con cuenta registrada).
- Incluye utilidades para:
  - **Enfrentar dos modelos** entre sí o un modelo contra rivales de referencia: `battle_models.py`.
  - **Arrancar self-play** desde un modelo ya entrenado, sin sobrescribirlo: `selfplay_from.py`.
  - **Exportar las gráficas** de TensorBoard a PNG con etiquetas y ejes en español: `plot_metrics.py`.
  - **Añadir formatos VGC vigentes** al servidor adaptado: `patch_server_formats.py`.

---

## Cómo navegar esta documentación

- **Paquetes** (barra lateral izquierda) — agrupa los módulos por carpeta (`src/`, raíz del proyecto). Cada módulo abre con su docstring, sus constantes globales y la lista de funciones y clases.
- **Clases** — listado de todas las clases del proyecto (entornos Gymnasium, jugadores, extractor Transformer, callback de TensorBoard, etc.) con su diagrama de herencia.
- **Archivos** — listado completo de los `.py` con acceso al código fuente coloreado y referencias cruzadas.
- **Buscador** (arriba a la derecha) — busca por nombre de función, clase, archivo o palabra suelta del cuerpo del código.

---

## Estructura del proyecto

```
src/                            Código fuente propio (módulos importables)
├── singles_env.py              MySinglesEnv  — entorno de combates individuales
├── doubles_env.py              MyDoublesEnv  — entorno de combates dobles VGC
├── rl_wrapper.py               OpponentSamplingEnv — envoltorio de un solo agente
├── features.py                 Construcción de la observación detallada
├── policy.py                   Argumentos de política MLP y extractor Transformer
├── callbacks.py                WinRateCallback para TensorBoard
├── poke_env_patch.py           Parche de poke-env (Behemoth Blade / Bash)
└── teams.py                    Constructor de equipos para los entornos de dobles

train_singles.py, train_doubles.py   Scripts de entrenamiento
play.py                          Aceptar desafíos en local o jugar en ladder
battle_models.py                 Enfrentar dos modelos o uno contra baselines
selfplay_from.py                 Arrancar self-play desde un modelo entrenado
plot_metrics.py                  Exportar gráficas de TensorBoard
patch_server_formats.py          Añadir formatos VGC vigentes al servidor
test_env.py                      Test rápido del entorno
check_teams.py                   Validador de equipos contra el servidor
```

---

## Más documentación

- `README.md` — versión completa del README del proyecto (con tabla de contenidos, requisitos, comandos y bibliotecas de terceros).
- `INSTALACION.txt` — guía paso a paso para reinstalar el proyecto en un equipo desde cero.
- `COMANDOS.txt` — recetario de comandos del proyecto por temas (entrenar, jugar, enfrentar modelos, métricas, etc.).
- `_build_release/README.md` — documentación de los scripts que generan el binario distribuible.
