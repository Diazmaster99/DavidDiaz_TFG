# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Constructores de equipos para los entornos.

RandomTeamBuilder elige un equipo aleatorio (de una carpeta de ficheros .txt
en formato Showdown) en CADA combate. Así cada batalla usa un equipo distinto
de tu lista, en lugar de repetir siempre el mismo (mirror match fijo).

Como el entorno comparte el mismo teambuilder entre los dos lados, cada lado
pide su equipo independientemente -> normalmente ambos lados llevan equipos
DIFERENTES en cada combate (no-mirror y variado).
"""

from __future__ import annotations

import random
from pathlib import Path

from poke_env.teambuilder.constant_teambuilder import ConstantTeambuilder
from poke_env.teambuilder.teambuilder import Teambuilder


class RandomTeamBuilder(Teambuilder):
    """
    Devuelve un equipo aleatorio en cada yield_team().

    :param teams_dir: carpeta con ficheros .txt, cada uno un equipo en
        formato Showdown (el que exporta el Teambuilder de la web).
    """

    def __init__(self, teams_dir: str | Path):
        teams_dir = Path(teams_dir)
        files = sorted(teams_dir.glob("*.txt"))
        if not files:
            raise FileNotFoundError(
                f"No se encontraron ficheros .txt en {teams_dir}\n"
                "Exporta equipos desde https://play.pokemonshowdown.com/teambuilder\n"
                "y guarda cada uno como un .txt en esa carpeta."
            )
        self.team_files = files
        self.packed_teams: list[str] = []
        for f in files:
            team_str = f.read_text(encoding="utf-8").strip()
            if not team_str:
                continue
            mons = self.parse_showdown_team(team_str)
            self.packed_teams.append(self.join_team(mons))
        if not self.packed_teams:
            raise ValueError(f"Todos los ficheros de {teams_dir} están vacios.")

    def yield_team(self) -> str:
        return random.choice(self.packed_teams)

    def __len__(self) -> int:
        return len(self.packed_teams)


def build_teambuilder(path: str | Path | None):
    """
    Construye el teambuilder adecuado según la ruta:
      - None            -> None (formatos aleatorios, sin equipo)
      - fichero .txt    -> ConstantTeambuilder (siempre el mismo equipo)
      - carpeta         -> RandomTeamBuilder (equipo aleatorio por combate)
    """
    if path is None:
        return None
    p = Path(path)
    if p.is_dir():
        return RandomTeamBuilder(p)
    team_str = p.read_text(encoding="utf-8")
    return ConstantTeambuilder(team_str)
