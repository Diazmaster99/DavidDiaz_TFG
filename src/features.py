# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Construcción de observaciones detalladas para los entornos (estilo vgc-bench).

La idea es dar al agente RL toda la información que tendría un jugador humano
(efectividades, clima, campo, prioridades, estados, boosts, stats, side
conditions, etc.) y dejar que la red aprenda sola qué hacer.

Se exponen dos funciones:
    build_singles_obs(battle) -> np.ndarray (SINGLES_OBS_SIZE,)
    build_doubles_obs(battle) -> np.ndarray (DOUBLES_OBS_SIZE,)

Diseño por bloques de tamaño FIJO (rellenando con ceros lo que no exista),
de modo que la observación siempre tiene la misma longitud.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from poke_env.battle.battle import Battle
from poke_env.battle.double_battle import DoubleBattle
from poke_env.data import GenData

_CHART = GenData.from_gen(9).type_chart

# --- Vocabularios (orden fijo para los one-hot) ---
TYPE_NAMES = [
    "NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE", "FIGHTING",
    "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST",
    "DRAGON", "DARK", "STEEL", "FAIRY",
]
TYPE_IDX = {n: i for i, n in enumerate(TYPE_NAMES)}
STATUS_NAMES = ["BRN", "FRZ", "PAR", "PSN", "SLP", "TOX"]
WEATHER_NAMES = [
    "DESOLATELAND", "DELTASTREAM", "HAIL", "PRIMORDIALSEA",
    "RAINDANCE", "SANDSTORM", "SNOWSCAPE", "SUNNYDAY",
]
FIELD_NAMES = [
    "ELECTRIC_TERRAIN", "GRASSY_TERRAIN", "MISTY_TERRAIN",
    "PSYCHIC_TERRAIN", "TRICK_ROOM", "GRAVITY",
]
SIDE_NAMES = [
    "TAILWIND", "REFLECT", "LIGHT_SCREEN", "AURORA_VEIL", "SAFEGUARD",
    "MIST", "STEALTH_ROCK", "SPIKES", "TOXIC_SPIKES", "STICKY_WEB",
]
BOOST_KEYS = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]
STAT_KEYS = ["hp", "atk", "def", "spa", "spd", "spe"]

# --- Tamaños de cada bloque ---
N_TYPES = len(TYPE_NAMES)                 # 18
GLOBAL_FEATS = len(WEATHER_NAMES) + len(FIELD_NAMES) + 1   # 8+6+1 = 15
SIDE_FEATS = len(SIDE_NAMES)              # 10
ACTIVE_FEATS = 3 + len(STATUS_NAMES) + N_TYPES + len(BOOST_KEYS) + len(STAT_KEYS)  # 40
RESERVE_FEATS = 2 + len(STATUS_NAMES) + N_TYPES                                    # 26
_MOVE_SCALARS = 11
MOVE_FEATS_SINGLES = _MOVE_SCALARS + 3 + N_TYPES + 1   # +1 efectividad = 33
MOVE_FEATS_DOUBLES = _MOVE_SCALARS + 3 + N_TYPES + 2   # +2 efectividades = 34

SINGLES_BENCH = 5
DOUBLES_BENCH = 4

SINGLES_OBS_SIZE = (
    GLOBAL_FEATS + 2 * SIDE_FEATS + 2 * ACTIVE_FEATS
    + 2 * SINGLES_BENCH * RESERVE_FEATS + 4 * MOVE_FEATS_SINGLES
)  # 507
DOUBLES_OBS_SIZE = (
    GLOBAL_FEATS + 2 * SIDE_FEATS + 4 * ACTIVE_FEATS
    + 2 * DOUBLES_BENCH * RESERVE_FEATS + 2 * 4 * MOVE_FEATS_DOUBLES
)  # 675


def singles_token_segments() -> list[tuple[str, int, int]]:
    """
    Layout del vector plano de singles como secuencia de TOKENS (kind, inicio, len).
    DEBE coincidir con el orden en que build_singles_obs concatena los bloques.
    Lo usa el extractor transformer para trocear la observación en entidades.
    """
    segs: list[tuple[str, int, int]] = []
    off = 0
    g = GLOBAL_FEATS + 2 * SIDE_FEATS         # global + 2 bandos = 1 token
    segs.append(("global", off, g)); off += g
    for _ in range(2):                        # activo propio, activo rival
        segs.append(("active", off, ACTIVE_FEATS)); off += ACTIVE_FEATS
    for _ in range(2 * SINGLES_BENCH):        # banco propio (5) + rival (5)
        segs.append(("reserve", off, RESERVE_FEATS)); off += RESERVE_FEATS
    for _ in range(4):                        # 4 movimientos del activo propio
        segs.append(("move", off, MOVE_FEATS_SINGLES)); off += MOVE_FEATS_SINGLES
    assert off == SINGLES_OBS_SIZE, f"{off} != {SINGLES_OBS_SIZE}"
    return segs


def doubles_token_segments() -> list[tuple[str, int, int]]:
    """Layout de tokens de dobles. Coincide con build_doubles_obs."""
    segs: list[tuple[str, int, int]] = []
    off = 0
    g = GLOBAL_FEATS + 2 * SIDE_FEATS
    segs.append(("global", off, g)); off += g
    for _ in range(4):                        # 2 activos propios + 2 rivales
        segs.append(("active", off, ACTIVE_FEATS)); off += ACTIVE_FEATS
    for _ in range(2 * DOUBLES_BENCH):        # banco propio (4) + rival (4)
        segs.append(("reserve", off, RESERVE_FEATS)); off += RESERVE_FEATS
    for _ in range(8):                        # 4 movimientos x 2 activos propios
        segs.append(("move", off, MOVE_FEATS_DOUBLES)); off += MOVE_FEATS_DOUBLES
    assert off == DOUBLES_OBS_SIZE, f"{off} != {DOUBLES_OBS_SIZE}"
    return segs


# ---------------------------------------------------------------------------
# Helpers de bajo nivel
# ---------------------------------------------------------------------------

def _active_names(container) -> set[str]:
    """Nombres de los enums activos en un dict/set/enum/None (clima, campo...)."""
    if not container:
        return set()
    if isinstance(container, dict):
        return {k.name for k in container}
    if isinstance(container, (set, list, tuple)):
        return {k.name for k in container}
    return {container.name}


def _coerce_float(value, default: float = 0.0) -> float:
    if value is True:
        return 1.0
    if value is False or value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0  # p.ej. self_switch = "copyvolatile"


def _type_multihot(mon) -> list[float]:
    vec = [0.0] * N_TYPES
    if mon is not None:
        for t in mon.types:
            if t is not None and t.name in TYPE_IDX:
                vec[TYPE_IDX[t.name]] = 1.0
    return vec


def _status_onehot(mon) -> list[float]:
    vec = [0.0] * len(STATUS_NAMES)
    if mon is not None and mon.status is not None and mon.status.name in STATUS_NAMES:
        vec[STATUS_NAMES.index(mon.status.name)] = 1.0
    return vec


def _boosts(mon) -> list[float]:
    if mon is None:
        return [0.0] * len(BOOST_KEYS)
    return [mon.boosts.get(k, 0) / 6.0 for k in BOOST_KEYS]


def _base_stats(mon) -> list[float]:
    if mon is None:
        return [0.0] * len(STAT_KEYS)
    return [(mon.base_stats.get(k, 0) or 0) / 255.0 for k in STAT_KEYS]


def _active_features(mon) -> list[float]:
    """Bloque de un Pokémon ACTIVO (propio o rival). Longitud = ACTIVE_FEATS."""
    if mon is None:
        return [0.0] * ACTIVE_FEATS
    feats = [
        mon.current_hp_fraction or 0.0,
        1.0 if mon.fainted else 0.0,
        1.0 if mon.is_terastallized else 0.0,
    ]
    feats += _status_onehot(mon)
    feats += _type_multihot(mon)
    feats += _boosts(mon)
    feats += _base_stats(mon)
    return feats


def _reserve_features(mon) -> list[float]:
    """Bloque de un Pokémon en el BANCO. Longitud = RESERVE_FEATS."""
    if mon is None:
        return [0.0] * RESERVE_FEATS
    feats = [
        mon.current_hp_fraction or 0.0,
        1.0 if mon.fainted else 0.0,
    ]
    feats += _status_onehot(mon)
    feats += _type_multihot(mon)
    return feats


def _move_features(move, opponents) -> list[float]:
    """
    Bloque de un movimiento + su efectividad contra cada rival de 'opponents'.
    Longitud = _MOVE_SCALARS + 3 (categoría) + N_TYPES + len(opponents).
    """
    n_opp = len(opponents)
    if move is None:
        return [0.0] * (_MOVE_SCALARS + 3 + N_TYPES + n_opp)

    acc = _coerce_float(move.accuracy, 1.0)
    max_pp = move.max_pp or 1
    pp_frac = (move.current_pp or 0) / max_pp
    scalars = [
        (move.base_power or 0) / 100.0,
        acc,
        (move.priority or 0) / 5.0,
        (move.crit_ratio or 0) / 6.0,
        _coerce_float(move.drain),
        _coerce_float(move.recoil),
        1.0 if move.force_switch else 0.0,
        _coerce_float(move.self_switch),
        1.0 if move.self_destruct is not None else 0.0,
        pp_frac,
        (move.expected_hits or 1) / 5.0,
    ]
    # Categoría one-hot: PHYSICAL, SPECIAL, STATUS
    category = [0.0, 0.0, 0.0]
    cat_idx = {"PHYSICAL": 0, "SPECIAL": 1, "STATUS": 2}.get(move.category.name)
    if cat_idx is not None:
        category[cat_idx] = 1.0
    # Tipo del movimiento one-hot
    move_type = [0.0] * N_TYPES
    if move.type is not None and move.type.name in TYPE_IDX:
        move_type[TYPE_IDX[move.type.name]] = 1.0
    # Efectividad de tipo contra cada rival
    eff = []
    for opp in opponents:
        if opp is None or move.type is None:
            eff.append(0.0)
        else:
            eff.append(
                move.type.damage_multiplier(
                    opp.type_1, opp.type_2, type_chart=_CHART
                )
            )
    return scalars + category + move_type + eff


def _moves_block(active_mon, opponents, move_feat_len: int) -> list[float]:
    """4 movimientos del Pokémon activo (rellenando con ceros si faltan)."""
    block: list[float] = []
    moves = []
    if active_mon is not None:
        moves = list(active_mon.moves.values())[:4]
    for i in range(4):
        mv = moves[i] if i < len(moves) else None
        block += _move_features(mv, opponents)
    assert len(block) == 4 * move_feat_len
    return block


def _global_features(battle) -> list[float]:
    feats: list[float] = []
    w = _active_names(battle.weather)
    feats += [1.0 if name in w else 0.0 for name in WEATHER_NAMES]
    f = _active_names(battle.fields)
    feats += [1.0 if name in f else 0.0 for name in FIELD_NAMES]
    feats.append(min(battle.turn / 20.0, 2.0))
    return feats


def _side_features(conditions) -> list[float]:
    active = _active_names(conditions)
    return [1.0 if name in active else 0.0 for name in SIDE_NAMES]


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def build_singles_obs(battle: Battle) -> npt.NDArray[np.float32]:
    own = battle.active_pokemon
    opp = battle.opponent_active_pokemon

    feats: list[float] = []
    feats += _global_features(battle)                      # 15
    feats += _side_features(battle.side_conditions)        # 10
    feats += _side_features(battle.opponent_side_conditions)  # 10
    feats += _active_features(own)                         # 40
    feats += _active_features(opp)                         # 40

    own_bench = [m for m in battle.team.values() if m is not own][:SINGLES_BENCH]
    for i in range(SINGLES_BENCH):
        feats += _reserve_features(own_bench[i] if i < len(own_bench) else None)
    opp_bench = [
        m for m in battle.opponent_team.values() if m is not opp
    ][:SINGLES_BENCH]
    for i in range(SINGLES_BENCH):
        feats += _reserve_features(opp_bench[i] if i < len(opp_bench) else None)

    feats += _moves_block(own, [opp], MOVE_FEATS_SINGLES)  # 4*33

    assert len(feats) == SINGLES_OBS_SIZE, f"{len(feats)} != {SINGLES_OBS_SIZE}"
    return np.array(feats, dtype=np.float32)


def build_doubles_obs(battle: DoubleBattle) -> npt.NDArray[np.float32]:
    own_active = list(battle.active_pokemon) + [None, None]
    opp_active = list(battle.opponent_active_pokemon) + [None, None]
    own0, own1 = own_active[0], own_active[1]
    opps = [opp_active[0], opp_active[1]]

    feats: list[float] = []
    feats += _global_features(battle)                      # 15
    feats += _side_features(battle.side_conditions)        # 10
    feats += _side_features(battle.opponent_side_conditions)  # 10
    feats += _active_features(own0)                        # 40
    feats += _active_features(own1)                        # 40
    feats += _active_features(opps[0])                     # 40
    feats += _active_features(opps[1])                     # 40

    active_set = {id(m) for m in (own0, own1) if m is not None}
    own_bench = [
        m for m in battle.team.values() if id(m) not in active_set
    ][:DOUBLES_BENCH]
    for i in range(DOUBLES_BENCH):
        feats += _reserve_features(own_bench[i] if i < len(own_bench) else None)
    opp_active_set = {id(m) for m in opps if m is not None}
    opp_bench = [
        m for m in battle.opponent_team.values() if id(m) not in opp_active_set
    ][:DOUBLES_BENCH]
    for i in range(DOUBLES_BENCH):
        feats += _reserve_features(opp_bench[i] if i < len(opp_bench) else None)

    # Movimientos de cada activo propio, con efectividad vs los 2 rivales
    feats += _moves_block(own0, opps, MOVE_FEATS_DOUBLES)  # 4*34
    feats += _moves_block(own1, opps, MOVE_FEATS_DOUBLES)  # 4*34

    assert len(feats) == DOUBLES_OBS_SIZE, f"{len(feats)} != {DOUBLES_OBS_SIZE}"
    return np.array(feats, dtype=np.float32)
