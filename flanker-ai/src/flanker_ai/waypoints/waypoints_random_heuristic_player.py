import random
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


class WaypointsRandomHeuristicPlayer:
    """
    Random Heuristic Player for waypoints.
    Logic:
    1. If an enemy is visible, fire at a random visible enemy.
    2. Else, move to a random movable waypoint.
    """

    @staticmethod
    def play(
        gs: WaypointsGraphGameState,
        depth: int = 0,  # Not used for random
    ) -> tuple[float, list[WaypointAction]]:
        actions = WaypointsRandomHeuristicPlayer._get_actions(gs)
        if len(actions) == 0:
            return WaypointsRandomHeuristicPlayer._evaluate(gs), []

        # For random heuristic, select a random action
        selected_action = random.choice(actions)
        # Simulate the action to get the score
        new_gs = WaypointsRandomHeuristicPlayer._copy_gs(gs)
        WaypointsRandomHeuristicPlayer.perform_action(new_gs, selected_action)
        score = WaypointsRandomHeuristicPlayer._evaluate(new_gs)
        return score, [selected_action]

    @staticmethod
    def _copy_gs(gs: WaypointsGraphGameState) -> WaypointsGraphGameState:
        from dataclasses import replace
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
                if action.interrupt_at_id is not None:
                    if current_unit.faction == InitiativeState.Faction.BLUE:
                        current_unit.status = CombatUnit.Status.PINNED
                    else:
                        current_unit.status = CombatUnit.Status.SUPPRESSED
                        gs.initiative = InitiativeState.Faction.RED if gs.initiative == InitiativeState.Faction.BLUE else InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
            case WaypointFireAction():
                enemy_unit = gs.combat_units[action.target_id]
                if enemy_unit.faction == InitiativeState.Faction.BLUE:
                    enemy_unit.status = CombatUnit.Status.PINNED
                    gs.initiative = InitiativeState.Faction.RED if gs.initiative == InitiativeState.Faction.BLUE else InitiativeState.Faction.BLUE
                else:
                    enemy_unit.status = CombatUnit.Status.SUPPRESSED
            case WaypointAssaultAction():
                enemy_unit = gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    gs.initiative = InitiativeState.Faction.RED if gs.initiative == InitiativeState.Faction.BLUE else InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = enemy_unit.current_waypoint_id
                    if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                        gs.combat_units.pop(action.target_id)
                    else:
                        gs.combat_units.pop(action.unit_id)
                        gs.initiative = InitiativeState.Faction.RED if gs.initiative == InitiativeState.Faction.BLUE else InitiativeState.Faction.BLUE

    @staticmethod
    def _get_actions(gs: WaypointsGraphGameState) -> list[WaypointAction]:
        actions: list[WaypointAction] = []
        for combat_unit_id, combat_unit in gs.combat_units.items():
            current_waypoint = gs.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != gs.initiative:
                continue

            # Fire actions if enemy visible
            fire_actions = []
            for enemy_id, enemy_unit in gs.combat_units.items():
                if enemy_unit.faction == combat_unit.faction:
                    continue
                if combat_unit.status in [CombatUnit.Status.ACTIVE, CombatUnit.Status.PINNED]:
                    if enemy_unit.current_waypoint_id in current_waypoint.visible_nodes:
                        fire_actions.append(
                            WaypointFireAction(
                                unit_id=combat_unit_id,
                                target_id=enemy_id,
                            )
                        )
            if fire_actions:
                # For heuristic, prefer fire
                actions.extend(fire_actions)
                continue  # If can fire, don't move

            # Move actions
            if combat_unit.status == CombatUnit.Status.ACTIVE:
                movable_nodes = list(current_waypoint.movable_paths.keys())
                for move_to_id in movable_nodes:
                    interrupt = WaypointsRandomHeuristicPlayer._get_move_interrupt(gs, combat_unit, move_to_id)
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
            if interrupt_at_id is not None:
                break
            for enemy_unit in gs.combat_units.values():
                if enemy_unit.faction == current_unit.faction:
                    continue
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    continue
                enemy_visible_nodes = gs.waypoints[enemy_unit.current_waypoint_id].visible_nodes
                if path_id in enemy_visible_nodes:
                    return path_id
        return None

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