# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Parche en memoria para un bug de poke-env con los movimientos que CAMBIAN DE ID
al cambiar de forma:

  - Zacian-Coronado:    Iron Head -> Behemoth Blade (behemothblade)
  - Zamazenta-Coronado: Iron Head -> Behemoth Bash  (behemothbash)

El servidor de Showdown reporta el movimiento con el id de la forma
(behemothblade/behemothbash), pero poke-env guarda en el moveset del Pokémon el
id BASE (ironhead). Las funciones de conversión orden<->acción de poke-env
construyen la lista de huecos a partir de ese moveset (con ironhead) y luego la
comparan con lo que envia/espera el servidor (behemothbash), de modo que fallan:

  - order_to_action (oponente):  [m.id for m in mvs].index('behemothbash')
        -> ValueError: 'behemothbash' is not in list
  - action_to_order (AGENTE):    crea '/choose move ironhead', que el servidor
        rechaza porque la jugada válida es '/choose move behemothbash'.

Es decir, el bug afecta a AMBOS sentidos: ni el oponente ni el propio agente
pueden usar Behemoth Blade/Bash (les sale jugada aleatoria ese turno).

Arreglo: 'reconciliar' el moveset conocido -> cuando la variante de forma
(behemothbash) aparece en available_moves, se usa esa (mismo hueco) en lugar del
id base (ironhead). Así los ids coinciden con los del servidor y la conversión
funciona en los dos sentidos. Se aplica monkeypatching a las funciones de
poke-env al llamar apply(); es idempotente y no altera el comportamiento de
ningún Pokémon que no tenga uno de estos movimientos de cambio de forma.
"""

from __future__ import annotations

import numpy as np

from poke_env.battle.pokemon import Pokemon
from poke_env.environment.doubles_env import DoublesEnv
from poke_env.environment.singles_env import SinglesEnv
from poke_env.player.battle_order import (
    DefaultBattleOrder,
    ForfeitBattleOrder,
    PassBattleOrder,
    SingleBattleOrder,
)
from poke_env.player.player import Player

# Movimientos que cambian de id por cambio de forma: variante de forma -> base.
_FORM_MOVE_FALLBACK = {
    "behemothblade": "ironhead",   # Zacian-Coronado
    "behemothbash": "ironhead",    # Zamazenta-Coronado
}


def _reconcile(active_mon, available_moves):
    """Lista de (hasta 4) movimientos conocidos del Pokémon, sustituyendo el
    movimiento BASE (p.ej. ironhead) por su VARIANTE DE FORMA (behemothbash)
    cuando está aparece en available_moves. Conserva el orden (= huecos). Si no
    hay ninguna variante de forma activa, devuelve el moveset tal cual."""
    known = list(active_mon.moves.values())[:4]
    by_base = {}
    for am in available_moves:
        base = _FORM_MOVE_FALLBACK.get(am.id)
        if base is not None:
            by_base[base] = am
    if not by_base:
        return known
    return [by_base.get(m.id, m) for m in known]


# ---------------------------------------------------------------------------
# DOBLES: parche de las dos funciones internas por posicion.

def _d_order_to_action_individual(order, battle, fake, pos):
    if isinstance(order.order, str):
        if isinstance(order, DefaultBattleOrder):
            return np.int64(-2)
        else:
            assert isinstance(order, PassBattleOrder)
            return np.int64(0)
    if not fake and str(order) not in [str(o) for o in battle.valid_orders[pos]]:
        raise ValueError(
            f"Invalid order from player {battle.player_username} in battle "
            f"{battle.battle_tag} at position {pos} - order {order} not in "
            f"action space {[str(o) for o in battle.valid_orders[pos]]}!"
        )
    if isinstance(order.order, Pokemon):
        action = [p.base_species for p in battle.team.values()].index(
            order.order.base_species
        ) + 1
    else:
        active_mon = battle.active_pokemon[pos]
        assert active_mon is not None
        available = battle.available_moves[pos]
        avail_ids = [m.id for m in available]
        known_moves = _reconcile(active_mon, available)
        known_ids = [m.id for m in known_moves]
        mvs = (
            available
            if len(avail_ids) == 1 and avail_ids[0] not in known_ids
            else known_moves
        )
        action = [m.id for m in mvs].index(order.order.id)
        target = order.move_target + 2
        if order.mega:
            gimmick = 1
        elif order.z_move:
            gimmick = 2
        elif order.dynamax:
            gimmick = 3
        elif order.terastallize:
            gimmick = 4
        else:
            gimmick = 0
        action = 1 + 6 + 5 * action + target + 20 * gimmick
    return np.int64(action)


def _d_action_to_order_individual(action, battle, fake, pos):
    if action == -2:
        return DefaultBattleOrder()
    elif action == 0:
        order = PassBattleOrder()
    elif action < 7:
        order = Player.create_order(list(battle.team.values())[action - 1])
    else:
        active_mon = battle.active_pokemon[pos]
        if active_mon is None:
            raise ValueError(
                f"Invalid order from player {battle.player_username} "
                f"in battle {battle.battle_tag} at position {pos} - action "
                f"specifies a move, but battle.active_pokemon is None!"
            )
        available = battle.available_moves[pos]
        avail_ids = [m.id for m in available]
        known_moves = _reconcile(active_mon, available)
        known_ids = [m.id for m in known_moves]
        mvs = (
            available
            if len(avail_ids) == 1 and avail_ids[0] not in known_ids
            else known_moves
        )
        if (action - 7) % 20 // 5 not in range(len(mvs)):
            raise ValueError(
                f"Invalid action {action} from player {battle.player_username} "
                f"in battle {battle.battle_tag} at position {pos} - action "
                f"specifies a move but the move index {(action - 7) % 20 // 5} "
                f"is out of bounds for available moves {mvs}!"
            )
        order = Player.create_order(
            mvs[(action - 7) % 20 // 5],
            move_target=(action.item() - 7) % 5 - 2,
            mega=(action - 7) // 20 == 1,
            z_move=(action - 7) // 20 == 2,
            dynamax=(action - 7) // 20 == 3,
            terastallize=(action - 7) // 20 == 4,
        )
    if not fake and str(order) not in [str(o) for o in battle.valid_orders[pos]]:
        raise ValueError(
            f"Invalid action {action} from player {battle.player_username} "
            f"in battle {battle.battle_tag} at position {pos} - order {order} "
            f"not in action space {[str(o) for o in battle.valid_orders[pos]]}!"
        )
    return order


# ---------------------------------------------------------------------------
# SINGLES: parche de las dos funciones públicas.

def _s_order_to_action(order, battle, fake=False, strict=True):
    try:
        if isinstance(order, DefaultBattleOrder):
            action = -2
        elif isinstance(order, ForfeitBattleOrder):
            action = -1
        else:
            assert isinstance(order, SingleBattleOrder)
            assert not isinstance(order.order, str)
            if not fake and str(order) not in [str(o) for o in battle.valid_orders]:
                raise ValueError(
                    f"Invalid order from player {battle.player_username} "
                    f"in battle {battle.battle_tag} - order {order} "
                    f"not in valid orders {[str(o) for o in battle.valid_orders]}!"
                )
            if isinstance(order.order, Pokemon):
                action = [p.base_species for p in battle.team.values()].index(
                    order.order.base_species
                )
            else:
                assert battle.active_pokemon is not None
                available = battle.available_moves
                avail_ids = [m.id for m in available]
                known_moves = _reconcile(battle.active_pokemon, available)
                known_ids = [m.id for m in known_moves]
                mvs = (
                    available
                    if len(avail_ids) == 1 and avail_ids[0] not in known_ids
                    else known_moves
                )
                action = [m.id for m in mvs].index(order.order.id)
                if order.mega:
                    gimmick = 1
                elif order.z_move:
                    gimmick = 2
                elif order.dynamax:
                    gimmick = 3
                elif order.terastallize:
                    gimmick = 4
                else:
                    gimmick = 0
                action = 6 + action + 4 * gimmick
        return np.int64(action)
    except ValueError as e:
        if strict:
            raise e
        else:
            if battle.logger is not None:
                battle.logger.warning(str(e) + " Defaulting to random move.")
            return SinglesEnv.order_to_action(
                Player.choose_random_singles_move(battle), battle, fake, strict
            )


def _s_action_to_order(action, battle, fake=False, strict=True):
    try:
        if action == -2:
            return DefaultBattleOrder()
        elif action == -1:
            return ForfeitBattleOrder()
        elif action < 6:
            order = Player.create_order(list(battle.team.values())[action])
        else:
            if battle.active_pokemon is None:
                raise ValueError(
                    f"Invalid order from player {battle.player_username} "
                    f"in battle {battle.battle_tag} - action specifies a "
                    f"move, but battle.active_pokemon is None!"
                )
            available = battle.available_moves
            avail_ids = [m.id for m in available]
            known_moves = _reconcile(battle.active_pokemon, available)
            known_ids = [m.id for m in known_moves]
            mvs = (
                available
                if len(avail_ids) == 1 and avail_ids[0] not in known_ids
                else known_moves
            )
            if (action - 6) % 4 not in range(len(mvs)):
                raise ValueError(
                    f"Invalid action {action} from player {battle.player_username} "
                    f"in battle {battle.battle_tag} - action specifies a move "
                    f"but the move index {(action - 6) % 4} is out of bounds "
                    f"for available moves {mvs}!"
                )
            order = Player.create_order(
                mvs[(action - 6) % 4],
                mega=10 <= action.item() < 14,
                z_move=14 <= action.item() < 18,
                dynamax=18 <= action.item() < 22,
                terastallize=22 <= action.item() < 26,
            )
        if not fake and str(order) not in [str(o) for o in battle.valid_orders]:
            raise ValueError(
                f"Invalid action {action} from player {battle.player_username} "
                f"in battle {battle.battle_tag} - converted order {order} "
                f"not in valid orders {[str(o) for o in battle.valid_orders]}!"
            )
        return order
    except ValueError as e:
        if strict:
            raise e
        else:
            if battle.logger is not None:
                battle.logger.warning(str(e) + " Defaulting to random move.")
            return Player.choose_random_singles_move(battle)


# ---------------------------------------------------------------------------

_applied = False


def apply():
    """Aplica el parche (idempotente)."""
    global _applied
    if _applied:
        return
    DoublesEnv._order_to_action_individual = staticmethod(_d_order_to_action_individual)
    DoublesEnv._action_to_order_individual = staticmethod(_d_action_to_order_individual)
    SinglesEnv.order_to_action = staticmethod(_s_order_to_action)
    SinglesEnv.action_to_order = staticmethod(_s_action_to_order)
    _applied = True


# Se aplica automáticamente al importar el modulo (idempotente).
apply()
