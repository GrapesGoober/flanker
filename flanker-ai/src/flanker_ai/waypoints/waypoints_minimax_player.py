import random
from dataclasses import replace
from itertools import count
from typing import Iterator

from flanker_ai.waypoints.models import (
    AbstractedCombatUnit,
    WaypointAction,
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
    have RNG, determinism, or other fancier rigs. The MAX player is BLUE
    this the MIN player is RED.
    """

    @staticmethod
    def play(
        gs: WaypointsGraphGameState,
        depth: int,
        alpha: float = float("-inf"),
        beta: float = float("inf"),
        iter_counter: Iterator[int] | None = None,
    ) -> tuple[float, list[WaypointAction]]:

        actions = WaypointsMinimaxPlayer._get_actions(gs)
        if depth == 0 or len(actions) == 0:
            return WaypointsMinimaxPlayer._evaluate(gs), []

        is_maximizing = gs.initiative == InitiativeState.Faction.BLUE
        best_score = float("-inf") if is_maximizing else float("inf")
        best_actions: list[WaypointAction] = []
        for action in actions:
            new_gs = WaypointsMinimaxPlayer._copy_gs(gs)
            WaypointsMinimaxPlayer.perform_action(new_gs, action)
            if not iter_counter:
                iter_counter = count(0)
            iter = next(iter_counter)
            if iter % 5000 == 0:
                print(f"Evaluated {iter=}")
            score, future_actions = WaypointsMinimaxPlayer.play(
                new_gs,
                depth - 1,
                alpha=alpha,
                beta=beta,
                iter_counter=iter_counter,
            )
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_actions = [action] + future_actions
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_actions = [action] + future_actions
                beta = min(beta, best_score)
            if alpha >= beta:
                break
        return best_score, best_actions

    @staticmethod
    def _copy_gs(gs: WaypointsGraphGameState) -> WaypointsGraphGameState:
        copied_units = {id: replace(unit) for id, unit in gs.combat_units.items()}
        return WaypointsGraphGameState(
            waypoints=gs.waypoints,
            combat_units=copied_units,
            initiative=gs.initiative,
        )

    @staticmethod
    def perform_action(
        gs: WaypointsGraphGameState,
        action: WaypointAction,
    ) -> None:
        current_unit = gs.combat_units[action.unit_id]
        match action:
            case WaypointMoveAction():
                # Check for move interrupts
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now
                    if current_unit.faction == InitiativeState.Faction.BLUE:
                        current_unit.status = CombatUnit.Status.PINNED
                    else:
                        current_unit.status = CombatUnit.Status.SUPPRESSED
                        # Move Failed
                        match gs.initiative:
                            case InitiativeState.Faction.BLUE:
                                gs.initiative = InitiativeState.Faction.RED
                            case InitiativeState.Faction.RED:
                                gs.initiative = InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = action.move_to_waypoint_id

            case WaypointFireAction():
                # Assumes determinic for now
                enemy_unit = gs.combat_units[action.target_id]
                if enemy_unit.faction == InitiativeState.Faction.BLUE:
                    enemy_unit.status = CombatUnit.Status.PINNED
                    # Firing failed
                    match gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            gs.initiative = InitiativeState.Faction.BLUE
                else:
                    enemy_unit.status = CombatUnit.Status.SUPPRESSED

            case WaypointAssaultAction():
                # Check for move interrupts
                enemy_unit = gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    match gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            gs.initiative = InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = enemy_unit.current_waypoint_id

                # Runs the assault dice roll. Assumes determinic for now
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    gs.combat_units.pop(action.target_id)
                else:
                    gs.combat_units.pop(action.unit_id)
                    # Assault failed
                    match gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            gs.initiative = InitiativeState.Faction.BLUE

    @staticmethod
    def _get_actions(gs: WaypointsGraphGameState) -> list[WaypointAction]:

        actions: list[WaypointAction] = []
        for combat_unit_id, combat_unit in gs.combat_units.items():
            current_waypoint = gs.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != gs.initiative:
                continue

            # Adds assault & fire actions
            for enemy_id, enemy_unit in gs.combat_units.items():

                # Add fire action if the enemy is on a visible node
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

                # Add an assault action
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    # Only assault there if it's movable
                    if (
                        enemy_unit.current_waypoint_id
                        not in current_waypoint.movable_paths.keys()
                    ):
                        continue
                    interrupt = WaypointsMinimaxPlayer._get_move_interrupt(
                        gs, combat_unit, enemy_unit.current_waypoint_id
                    )
                    actions.append(
                        WaypointAssaultAction(
                            unit_id=combat_unit_id,
                            target_id=enemy_id,
                            interrupt_at_id=interrupt,
                        )
                    )

            # Adds move actions later, for best alpha-beta pruning
            if combat_unit.status == CombatUnit.Status.ACTIVE:
                # Filter some move actions to reduce branching factor
                movable_nodes = random.sample(
                    population=list(current_waypoint.movable_paths.keys()),
                    k=10,
                )

                for move_to_id in movable_nodes:
                    interrupt = WaypointsMinimaxPlayer._get_move_interrupt(
                        gs, combat_unit, move_to_id
                    )
                    actions.append(
                        WaypointMoveAction(
                            unit_id=combat_unit_id,
                            move_to_waypoint_id=move_to_id,
                            interrupt_at_id=interrupt,
                        )
                    )

        return actions

    @staticmethod
    def _get_move_interrupt(
        gs: WaypointsGraphGameState,
        current_unit: AbstractedCombatUnit,
        move_to_id: int,
    ) -> int | None:
        interrupt_at_id: int | None = None
        current_waypoint = gs.waypoints[current_unit.current_waypoint_id]
        for path_id in current_waypoint.movable_paths[move_to_id]:
            if interrupt_at_id is not None:  # If found interrupt, stop search
                break
            for enemy_unit in gs.combat_units.values():
                # Add interrupt if the enemy can reactive fire it
                if enemy_unit.faction == current_unit.faction:
                    continue
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    continue
                enemy_visible_nodes = gs.waypoints[
                    enemy_unit.current_waypoint_id
                ].visible_nodes
                if path_id in enemy_visible_nodes:
                    return path_id

    @staticmethod
    def _evaluate(gs: WaypointsGraphGameState) -> float:
        """Heuristic valuation from BLUE perspective"""
        score = 0.0
        for unit in gs.combat_units.values():
            value = 0
            match unit.status:
                case CombatUnit.Status.ACTIVE:
                    value = 3
                case CombatUnit.Status.PINNED:
                    value = 2
                case CombatUnit.Status.SUPPRESSED:
                    value = 1

            if unit.faction == InitiativeState.Faction.BLUE:
                score += value
            else:
                score -= value
        return score
