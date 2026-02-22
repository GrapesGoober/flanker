import random

from flanker_ai.waypoints.models import (
    AbstractedCombatUnit,
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
    WaypointsGraphGameState,
)
from flanker_ai.waypoints.waypoints_scheme import replace
from flanker_core.models.components import CombatUnit, InitiativeState


class WaypointsMinimaxSearch:
    """
    Implements a basic abstracted waypoints-graph expectimax AI search.
    """

    @staticmethod
    def search_best_action(
        gs: WaypointsGraphGameState,
        depth: int,
        alpha: float = float("-inf"),
        beta: float = float("inf"),
    ) -> tuple[float, WaypointAction | None]:

        winner = WaypointsMinimaxSearch._get_winning_faction(gs)
        # Have it prefer earlier win
        if winner == InitiativeState.Faction.BLUE:
            return 10000 + depth, None
        elif winner == InitiativeState.Faction.RED:
            return -10000 - depth, None

        actions = WaypointsMinimaxSearch._get_actions(gs)
        if depth == 0 or len(actions) == 0:
            return WaypointsMinimaxSearch._evaluate(gs), None

        is_maximizing = gs.initiative == InitiativeState.Faction.BLUE
        best_score = float("-inf") if is_maximizing else float("inf")
        best_action: WaypointAction | None = None
        for action in actions:
            outcomes = WaypointsMinimaxSearch._perform_action(gs, action)
            expected_score = 0.0
            for prob, outcome_gs in outcomes:
                score, _ = WaypointsMinimaxSearch.search_best_action(
                    outcome_gs,
                    depth - 1,
                    alpha=alpha,
                    beta=beta,
                )
                expected_score += prob * score

            # TODO: expected_score doesnt work optimally for pruning
            if is_maximizing:
                if expected_score > best_score:
                    best_score = expected_score
                    best_action = action
                if best_score >= beta:
                    break
                alpha = max(alpha, best_score)
            else:
                if expected_score < best_score:
                    best_score = expected_score
                    best_action = action
                if best_score <= alpha:
                    break
                beta = min(beta, best_score)
        return best_score, best_action

    @staticmethod
    def _copy_gs(gs: WaypointsGraphGameState) -> WaypointsGraphGameState:
        copied_units = {id: replace(unit) for id, unit in gs.combat_units.items()}
        copied_objectives = [replace(obj) for obj in gs.objectives]
        return WaypointsGraphGameState(
            waypoints=gs.waypoints,
            combat_units=copied_units,
            initiative=gs.initiative,
            objectives=copied_objectives,
        )

    @staticmethod
    def _perform_action(
        gs: WaypointsGraphGameState,
        action: WaypointAction,
    ) -> list[tuple[float, WaypointsGraphGameState]]:
        match action:
            case WaypointMoveAction():
                new_gs = WaypointsMinimaxSearch._copy_gs(gs)
                current_unit = new_gs.combat_units[action.unit_id]
                # Check for move interrupts
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now
                    current_unit.status = CombatUnit.Status.PINNED
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                return [(1, new_gs)]

            case WaypointFireAction():
                # Assumes determinic for now
                new_gs = WaypointsMinimaxSearch._copy_gs(gs)
                target_unit = new_gs.combat_units[action.target_id]
                target_unit.status = CombatUnit.Status.SUPPRESSED
                return [(1, new_gs)]

            case WaypointAssaultAction():
                new_gs = WaypointsMinimaxSearch._copy_gs(gs)
                current_unit = new_gs.combat_units[action.unit_id]
                # Check for move interrupts
                target_unit = new_gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    match new_gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            new_gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            new_gs.initiative = InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = target_unit.current_waypoint_id

                # Runs the assault dice roll. Assumes determinic for now
                killed_unit: AbstractedCombatUnit
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    new_gs.combat_units.pop(action.target_id)
                    killed_unit = target_unit
                else:
                    killed_unit = current_unit
                    new_gs.combat_units.pop(action.unit_id)
                    # Assault failed
                    match new_gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            new_gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            new_gs.initiative = InitiativeState.Faction.BLUE

                for objective in new_gs.objectives:
                    if killed_unit.faction == objective.target_faction:
                        objective.units_destroyed_counter += 1

                return [(1, new_gs)]

    @staticmethod
    def _get_actions(gs: WaypointsGraphGameState) -> list[WaypointAction]:

        actions: list[WaypointAction] = []
        friendly_units: list[tuple[int, AbstractedCombatUnit]] = []
        enemy_units: list[tuple[int, AbstractedCombatUnit]] = []
        for combat_unit_id, combat_unit in gs.combat_units.items():
            if combat_unit.faction == gs.initiative:
                friendly_units.append((combat_unit_id, combat_unit))
            if combat_unit.faction != gs.initiative:
                enemy_units.append((combat_unit_id, combat_unit))

        for combat_unit_id, combat_unit in friendly_units:
            current_waypoint = gs.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != gs.initiative:
                continue

            # Adds assault & fire actions
            for enemy_id, enemy_unit in enemy_units:

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
                    interrupt = WaypointsMinimaxSearch._get_move_interrupt(
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
            # TODO: is this causing the speed decrease for 3v3?
            # It creates new population list every branch
            if combat_unit.status == CombatUnit.Status.ACTIVE:
                # Filter some move actions to reduce branching factor
                movable_nodes = random.sample(
                    population=list(current_waypoint.movable_paths.keys()),
                    k=10,
                )

                for move_to_id in movable_nodes:
                    interrupt = WaypointsMinimaxSearch._get_move_interrupt(
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
        current_waypoint = gs.waypoints[current_unit.current_waypoint_id]
        for path_id in current_waypoint.movable_paths[move_to_id]:
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
        return None

    @staticmethod
    def _evaluate(gs: WaypointsGraphGameState) -> float:
        """Heuristic non-terminal valuation from BLUE perspective"""
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

    @staticmethod
    def _get_winning_faction(
        gs: WaypointsGraphGameState,
    ) -> InitiativeState.Faction | None:
        """If terminal, returns which faction wins."""
        for objective in gs.objectives:
            if objective.units_to_destroy == objective.units_destroyed_counter:
                return objective.winning_faction
        return None
