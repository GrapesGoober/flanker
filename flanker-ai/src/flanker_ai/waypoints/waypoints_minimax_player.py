from dataclasses import replace
from itertools import count
from typing import Iterator

from flanker_ai.waypoints.models import (
    WaypointActions,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
    WaypointsGraphGameState,
)
from flanker_core.models.components import CombatUnit, InitiativeState


class WaypointsMinimaxPlayer:
    """
    Implements a basic abstracted waypoints-graph minimax AI player.
    This is just a bare minimum code for the CoG paper, thus doesn't
    have RNG, determinism, or other fancier rigs.
    """

    @staticmethod
    def play(
        gs: WaypointsGraphGameState,
        depth: int,
        iter_counter: Iterator[int] | None = None,
    ) -> tuple[float, list[WaypointActions]]:
        actions = WaypointsMinimaxPlayer._get_actions(gs)
        if depth == 0 or len(actions) == 0:
            return WaypointsMinimaxPlayer._evaluate(gs), []

        best_score = float("-inf")
        best_actions: list[WaypointActions] = []
        for action in actions:
            new_gs = WaypointsMinimaxPlayer._copy_gs(gs)
            WaypointsMinimaxPlayer.perform_action(new_gs, action)
            if not iter_counter:
                iter_counter = count(0)
            iter = next(iter_counter)
            if iter % 100 == 0:
                print(f"Evaluated {iter=}")
            score, actions = WaypointsMinimaxPlayer.play(
                new_gs,
                depth - 1,
                iter_counter=iter_counter,
            )
            if score > best_score:
                best_score = score
                best_actions = [action] + actions
        return best_score, best_actions

    @staticmethod
    def _copy_gs(gs: WaypointsGraphGameState) -> WaypointsGraphGameState:
        copied_units = {id: replace(unit) for id, unit in gs.combat_units.items()}
        return WaypointsGraphGameState(
            game_state=gs.game_state,
            waypoints=gs.waypoints,
            combat_units=copied_units,
            initiative=gs.initiative,
        )

    @staticmethod
    def perform_action(
        gs: WaypointsGraphGameState,
        action: WaypointActions,
    ) -> None:
        current_unit = gs.combat_units[action.unit_id]
        match action:
            case WaypointMoveAction():
                # Check for move interrupts
                is_interrupted = False
                for enemy_unit in gs.combat_units.values():
                    if enemy_unit.faction == current_unit.faction:
                        continue
                    target_waypoint = gs.waypoints[action.move_to_waypoint_id]
                    if enemy_unit.current_waypoint_id in target_waypoint.visible_nodes:
                        is_interrupted = True
                        break
                if is_interrupted:
                    # Assumes determinic for now
                    if current_unit.faction == InitiativeState.Faction.BLUE:
                        current_unit.status = CombatUnit.Status.PINNED
                    else:
                        current_unit.status = CombatUnit.Status.SUPPRESSED
                # Assume that the target waypoint becomes move interrupt
                current_unit.current_waypoint_id = action.move_to_waypoint_id

            case WaypointFireAction():
                # Assumes determinic for now
                enemy_unit = gs.combat_units[action.target_id]
                if enemy_unit.faction == InitiativeState.Faction.BLUE:
                    enemy_unit.status = CombatUnit.Status.PINNED
                else:
                    enemy_unit.status = CombatUnit.Status.SUPPRESSED

            case WaypointAssaultAction():
                # Assumes determinic for now
                enemy_unit = gs.combat_units[action.target_id]
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    gs.combat_units.pop(action.target_id)
                else:
                    gs.combat_units.pop(action.unit_id)

    @staticmethod
    def _get_actions(gs: WaypointsGraphGameState) -> list[WaypointActions]:

        actions: list[WaypointActions] = []
        for combat_unit_id, combat_unit in gs.combat_units.items():
            current_waypoint = gs.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != gs.initiative:
                continue

            # Adds move actions
            if combat_unit.status == CombatUnit.Status.ACTIVE:
                for movable_node_id in current_waypoint.movable_nodes:
                    actions.append(
                        WaypointMoveAction(
                            unit_id=combat_unit_id,
                            move_to_waypoint_id=movable_node_id,
                        )
                    )
                # FIXME: have it only append RELEVANT nodes, not just distance
                # Otherwise there's too high branching factor while missing waypoint 51
                actions.append(
                    WaypointMoveAction(
                        unit_id=combat_unit_id,
                        move_to_waypoint_id=51,
                    )
                )
            # Adds assault & fire actions
            for enemy_id, enemy_unit in gs.combat_units.items():
                if enemy_unit.faction == combat_unit.faction:
                    continue
                if combat_unit.status in [
                    CombatUnit.Status.ACTIVE,
                    CombatUnit.Status.PINNED,
                ]:
                    if enemy_unit.current_waypoint_id in current_waypoint.visible_nodes:
                        actions.append(
                            WaypointFireAction(
                                unit_id=combat_unit_id,
                                target_id=enemy_id,
                            )
                        )
                # FIXME: Technically, there should be MOVABLE check
                # TODO: add move interrupt to assault action
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    actions.append(
                        WaypointAssaultAction(
                            unit_id=combat_unit_id,
                            target_id=enemy_id,
                        )
                    )

        return actions

    @staticmethod
    def _evaluate(gs: WaypointsGraphGameState) -> float:
        score: float = 0.0
        for unit in gs.combat_units.values():
            if unit.faction == gs.initiative:
                match unit.status:
                    case CombatUnit.Status.ACTIVE:
                        score += 3
                    case CombatUnit.Status.PINNED:
                        score += 2
                    case CombatUnit.Status.SUPPRESSED:
                        score += 1
            else:
                match unit.status:
                    case CombatUnit.Status.ACTIVE:
                        score -= 3
                    case CombatUnit.Status.PINNED:
                        score -= 2
                    case CombatUnit.Status.SUPPRESSED:
                        score -= 1
        return score
