# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Script de prueba rápida del entorno.

Verifica que los entornos se crean correctamente y que se puede
ejecutar un paso de entrenamiento sin errores.

Uso:
    python test_env.py          # prueba singles
    python test_env.py --doubles # prueba doubles (necesitas --team)
    python test_env.py --doubles --team teams/vgc/equipo1.txt

Necesita el servidor Showdown corriendo:
    node pokemon-showdown start --no-security
"""

import argparse
import time

import numpy as np
from stable_baselines3.common.env_checker import check_env


def test_singles(port: int):
    from src.singles_env import SinglesGymEnv, SINGLES_OBS_SIZE

    print("--- Prueba entorno Singles ---")
    print(f"Conectando al servidor en el puerto {port}...")

    env = SinglesGymEnv(port=port, battle_format="gen9randombattle", log_level=30)

    print(f"Espacio de observación: {env.observation_space}")
    print(f"Espacio de acción: {env.action_space}")
    assert env.observation_space.shape == (SINGLES_OBS_SIZE,), \
        f"Dimensión incorrecta: {env.observation_space.shape}"

    print("Verificando compatibilidad con Gymnasium (check_env)...")
    # check_env hace algunos resets y steps para verificar la API
    # Nota: puede tardar unos segundos esperando al servidor
    check_env(env, warn=True, skip_render_check=True)
    print("check_env: OK")

    print("Ejecutando un episodio completo...")
    obs, info = env.reset()
    assert obs.shape == (SINGLES_OBS_SIZE,)
    steps = 0
    start = time.time()
    while True:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        steps += 1
        if terminated or truncated:
            break
        if time.time() - start > 60:
            print("Timeout (60s) - abortando episodio")
            break

    elapsed = time.time() - start
    print(f"Episodio completado: {steps} pasos en {elapsed:.1f}s")
    print(f"Tasa de victorias: {env.win_rate:.2%}")
    env.close()
    print("Test singles: PASADO\n")


def test_doubles(port: int, team_path: str):
    from src.doubles_env import DoublesGymEnv, DOUBLES_OBS_SIZE

    print("--- Prueba entorno Doubles VGC ---")
    print(f"Equipo: {team_path}")
    print(f"Conectando al servidor en el puerto {port}...")

    env = DoublesGymEnv(
        port=port,
        battle_format="gen9vgc2025regg",
        log_level=30,
        team_path=team_path,
    )

    print(f"Espacio de observación: {env.observation_space}")
    print(f"Espacio de acción: {env.action_space}")
    assert env.observation_space.shape == (DOUBLES_OBS_SIZE,), \
        f"Dimensión incorrecta: {env.observation_space.shape}"

    print("Ejecutando un episodio de prueba...")
    obs, info = env.reset()
    steps = 0
    start = time.time()
    while True:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        steps += 1
        if terminated or truncated:
            break
        if time.time() - start > 120:
            print("Timeout (120s) - abortando episodio")
            break

    elapsed = time.time() - start
    print(f"Episodio completado: {steps} pasos en {elapsed:.1f}s")
    env.close()
    print("Test doubles: PASADO\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--doubles", action="store_true")
    parser.add_argument("--team", type=str, default=None)
    args = parser.parse_args()

    if args.doubles:
        if args.team is None:
            print("ERROR: Para el test de doubles necesitas --team FICHERO")
            print("Ejemplo: python test_env.py --doubles --team teams/vgc/equipo1.txt")
            exit(1)
        test_doubles(args.port, args.team)
    else:
        test_singles(args.port)
