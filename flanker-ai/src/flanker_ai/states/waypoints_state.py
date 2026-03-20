import math
import random
from copy import deepcopy
from dataclasses import dataclass, replace
from itertools import product
from math import prod
from typing import Literal, override

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.waypoints_actions import (
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
    WaypointPivotAction,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter

_FIRE_ACTION_PROBABILITIES = {
    FireOutcomes.PIN: 0.4,
    FireOutcomes.SUPPRESS: 0.6,
}

_FIRE_REACTION_PROBABILITIES = {
    FireOutcomes.PIN: 0.6,
    FireOutcomes.SUPPRESS: 0.4,
}

_MAX_STALL_LIMIT = 5


@dataclass
class _AbstractedCombatUnit:
    # Note: this should be kept flat to be serializable
    unit_id: int
    current_waypoint_id: int
    degrees: float
    status: CombatUnit.Status
    faction: InitiativeState.Faction
    no_fire: bool


@dataclass
class _WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


class WaypointsState(IRepresentationState[WaypointAction]):
    def __init__(
        self,
        points: list[Vec2],
        path_tolerance: float,
    ) -> None:
        self._points = points
        self.waypoints: dict[int, _WaypointNode] = {}
        self.combat_units: dict[int, _AbstractedCombatUnit] = {}
        self._initiative: InitiativeState.Faction = InitiativeState.Faction.BLUE
        self._objectives: list[EliminationObjective] = []
        self._path_tolerance = path_tolerance
        self._stall_counter: dict[InitiativeState.Faction, int] = {
            InitiativeState.Faction.BLUE: 0,
            InitiativeState.Faction.RED: 0,
        }

    @override
    def copy(self) -> "WaypointsState":
        copied_units = {id: replace(unit) for id, unit in self.combat_units.items()}
        copied_objectives = [replace(obj) for obj in self._objectives]
        new_gs = WaypointsState(
            points=self._points,
            path_tolerance=self._path_tolerance,
        )
        new_gs.waypoints = self.waypoints
        new_gs.combat_units = copied_units
        new_gs._initiative = self._initiative
        new_gs._objectives = copied_objectives
        new_gs._stall_counter = deepcopy(self._stall_counter)
        return new_gs

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        return self._initiative

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for unit in self.combat_units.values():
            value = 0
            match unit.status:
                case CombatUnit.Status.ACTIVE:
                    value = 3
                case CombatUnit.Status.PINNED:
                    value = 2
                case CombatUnit.Status.SUPPRESSED:
                    value = 1

            if unit.faction == maximizing_faction:
                score += value
            else:
                score -= value
        return score

    @override
    def get_actions(self) -> list[WaypointAction]:

        actions: list[WaypointAction] = []
        friendly_units: list[tuple[int, _AbstractedCombatUnit]] = []
        enemy_units: list[tuple[int, _AbstractedCombatUnit]] = []
        for combat_unit_id, combat_unit in self.combat_units.items():
            if combat_unit.faction == self._initiative:
                friendly_units.append((combat_unit_id, combat_unit))
            if combat_unit.faction != self._initiative:
                enemy_units.append((combat_unit_id, combat_unit))

        for friendly_id, friendly_unit in friendly_units:
            friendly_waypoint = self.waypoints[friendly_unit.current_waypoint_id]
            if friendly_unit.faction != self._initiative:
                continue

            # Adds assault & fire actions
            for enemy_id, enemy_unit in enemy_units:
                if enemy_unit.faction == friendly_unit.faction:
                    continue

                # Fire action possible, check for criteria
                if friendly_unit.status in [
                    CombatUnit.Status.ACTIVE,
                    CombatUnit.Status.PINNED,
                ]:
                    if (  # Firable only for visible enemies
                        enemy_unit.current_waypoint_id
                        not in friendly_waypoint.visible_nodes
                    ):
                        continue

                    enemy_waypoint = self.waypoints[enemy_unit.current_waypoint_id]
                    if not LosSystem.in_fov(  # Firable only for within FOV
                        Transform(friendly_waypoint.position, friendly_unit.degrees),
                        enemy_waypoint.position,
                    ):
                        continue

                    actions.append(
                        WaypointFireAction(
                            unit_id=friendly_id,
                            target_id=enemy_id,
                        )
                    )

                # Add an assault action
                if friendly_unit.status == CombatUnit.Status.ACTIVE:
                    # Only assault there if it's movable
                    if (
                        enemy_unit.current_waypoint_id
                        not in friendly_waypoint.movable_paths.keys()
                    ):
                        continue
                    actions.append(
                        WaypointAssaultAction(
                            unit_id=friendly_id,
                            target_id=enemy_id,
                        )
                    )

            # Add pivot actions; have it pivot towards enemies
            if friendly_unit.status == CombatUnit.Status.ACTIVE:
                for _, enemy_unit in enemy_units:
                    enemy_waypoint = self.waypoints[enemy_unit.current_waypoint_id]
                    if LosSystem.in_fov(
                        Transform(friendly_waypoint.position, friendly_unit.degrees),
                        enemy_waypoint.position,
                    ):
                        continue
                    # TODO: temporary fix to make running trials faster.
                    # If the target isn't in LOS, don't need to pivot.
                    if (
                        enemy_unit.current_waypoint_id
                        not in friendly_waypoint.visible_nodes
                    ):
                        continue
                    actions.append(
                        WaypointPivotAction(
                            unit_id=friendly_id,
                            pivot_to_waypoint_id=enemy_unit.current_waypoint_id,
                        )
                    )

            # Adds move actions later, for best alpha-beta pruning
            # TODO: is this causing the speed decrease for 3v3?
            # It creates new population list every branch
            if friendly_unit.status == CombatUnit.Status.ACTIVE:
                # Collect occupied waypoint IDs
                occupied_waypoints: set[int] = {
                    combat_unit.current_waypoint_id
                    for combat_unit in self.combat_units.values()
                }

                # Filter move actions so we don't move to occupied waypoints
                available_waypoints: list[int] = [
                    wid
                    for wid in friendly_waypoint.movable_paths.keys()
                    if wid not in occupied_waypoints
                ]

                # Randomly sample to reduce branching factor
                movable_nodes = random.sample(
                    population=available_waypoints,
                    k=min(9, len(available_waypoints)),
                )

                for move_to_id in movable_nodes:
                    actions.append(
                        WaypointMoveAction(
                            unit_id=friendly_id,
                            move_to_waypoint_id=move_to_id,
                        )
                    )

        return actions

    # TODO: this should be removed. It's duplicate code.
    # Currently the reactive fire uses deterministic outcome.
    # I still want this to handle peeking.
    @override
    def get_deterministic_branch(
        self,
        action: WaypointAction,
    ) -> "WaypointsState":

        match action:
            case WaypointMoveAction():
                rs = self.copy()
                rs._pivot_towards(action.unit_id, action.move_to_waypoint_id)
                current_unit = rs.combat_units[action.unit_id]
                # Check for move interrupts
                interrupts = rs.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=action.move_to_waypoint_id,
                )
                if interrupts != []:
                    num_shooters = len(interrupts[0][1])
                    rs._stall_counter[rs._initiative] = 0
                    # Assumes determinic for now
                    if num_shooters == 1:
                        current_unit.status = CombatUnit.Status.PINNED
                    elif num_shooters > 1:
                        current_unit.status = CombatUnit.Status.SUPPRESSED
                    current_unit.current_waypoint_id = interrupts[0][0]
                else:
                    rs._stall_counter[rs._initiative] += 1
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                return rs

            case WaypointPivotAction():
                rs = self.copy()
                rs._pivot_towards(action.unit_id, action.pivot_to_waypoint_id)
                current_unit = rs.combat_units[action.unit_id]
                # Check for move interrupts
                interrupts = self.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=None,
                )
                if interrupts != []:
                    num_shooters = len(interrupts[0][1])
                    rs._stall_counter[rs._initiative] = 0
                    # Assumes determinic for now
                    if num_shooters == 1:
                        current_unit.status = CombatUnit.Status.PINNED
                    elif num_shooters > 1:
                        current_unit.status = CombatUnit.Status.SUPPRESSED
                    current_unit.current_waypoint_id = interrupts[0][0]
                else:
                    rs._stall_counter[rs._initiative] += 1
                return rs

            case WaypointFireAction():
                rs = self.copy()
                rs._stall_counter[rs._initiative] = 0
                # Assumes determinic for now
                target_unit = rs.combat_units[action.target_id]
                target_unit.status = CombatUnit.Status.SUPPRESSED
                return rs

            case WaypointAssaultAction():
                rs = self.copy()
                rs._stall_counter[rs._initiative] = 0
                # Check for move interrupts
                current_unit = rs.combat_units[action.unit_id]
                target_unit = rs.combat_units[action.target_id]
                target_waypoint = target_unit.current_waypoint_id
                rs._pivot_towards(action.unit_id, target_waypoint)
                interrupts = rs.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=target_waypoint,
                )
                if interrupts != []:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    rs._flip_initiative()
                    current_unit.current_waypoint_id = interrupts[0][0]
                else:
                    current_unit.current_waypoint_id = target_waypoint

                # Runs the assault dice roll. Assumes determinic for now
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    rs._kill_unit(target_unit.unit_id)
                else:
                    rs._kill_unit(current_unit.unit_id)
                    # Assault failed
                    rs._flip_initiative()

                return rs

    def get_all_fire_permutations(
        self, enemy_ids: list[int]
    ) -> list[tuple[float, dict[int, FireOutcomes]]]:
        """Returns all permutations of (unit, outcome) and their probabilities."""
        permutations: list[
            tuple[
                float,  # total probability of this permutation event
                dict[int, FireOutcomes],  # event (key=enemy, value=outcome)
            ]
        ] = []

        # Assemble the probability and fire outcomes
        outcomes = list(_FIRE_REACTION_PROBABILITIES.keys())
        for outcome_combo in product(outcomes, repeat=len(enemy_ids)):
            probability = prod(
                _FIRE_REACTION_PROBABILITIES[outcome] for outcome in outcome_combo
            )
            event = {
                enemy_id: outcome for enemy_id, outcome in zip(enemy_ids, outcome_combo)
            }
            permutations.append((probability, event))
        return permutations

    @override
    def get_branches(
        self, action: WaypointAction
    ) -> list[tuple[float, "WaypointsState"]]:
        match action:
            case WaypointMoveAction():
                rs = self.copy()
                rs._pivot_towards(action.unit_id, action.move_to_waypoint_id)

                interrupts = rs.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=action.move_to_waypoint_id,
                )
                if interrupts != []:
                    outcomes = rs._get_reactive_fire_outcomes(
                        interrupts, action.unit_id, action.move_to_waypoint_id
                    )
                    return outcomes
                else:  # No move interrupt found
                    rs._stall_counter[rs._initiative] += 1
                    rs._pivot_towards(action.unit_id, action.move_to_waypoint_id)
                    current_unit = rs.combat_units[action.unit_id]
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                    return [(1, rs)]

            case WaypointPivotAction():
                rs = self.copy()
                rs._pivot_towards(action.unit_id, action.pivot_to_waypoint_id)

                interrupts = rs.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=None,
                )
                if interrupts != []:
                    outcomes = rs._get_reactive_fire_outcomes(
                        interrupts, action.unit_id, move_to_id=None
                    )
                    return outcomes
                else:  # No move interrupt found
                    rs._stall_counter[rs._initiative] += 1
                    rs._pivot_towards(action.unit_id, action.pivot_to_waypoint_id)
                    return [(1, rs)]

            case WaypointFireAction():
                all_outcomes: list[tuple[float, "WaypointsState"]] = []
                for fire_outcome, probability in _FIRE_ACTION_PROBABILITIES.items():
                    rs = self.copy()
                    rs._stall_counter[rs._initiative] = 0
                    target_unit = rs.combat_units[action.target_id]
                    match fire_outcome:
                        case FireOutcomes.MISS:
                            rs._flip_initiative()
                        case FireOutcomes.PIN:
                            if target_unit.status == CombatUnit.Status.ACTIVE:
                                target_unit.status = CombatUnit.Status.PINNED
                            rs._flip_initiative()
                        case FireOutcomes.SUPPRESS:
                            target_unit.status = CombatUnit.Status.SUPPRESSED
                        case FireOutcomes.KILL:
                            rs._kill_unit(action.target_id)
                    all_outcomes.append((probability, rs))

                return all_outcomes

            case WaypointAssaultAction():  # Assumes determinic for now
                rs = self.copy()
                rs._stall_counter[rs._initiative] = 0
                # Check for move interrupts
                current_unit = rs.combat_units[action.unit_id]
                target_unit = rs.combat_units[action.target_id]
                rs._pivot_towards(action.unit_id, target_unit.current_waypoint_id)
                interrupts = rs.get_move_interrupts(
                    unit_id=action.unit_id,
                    move_to_id=target_unit.current_waypoint_id,
                )
                if interrupts != []:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    rs._flip_initiative()
                    current_unit.current_waypoint_id = interrupts[0][0]
                else:
                    current_unit.current_waypoint_id = target_unit.current_waypoint_id

                # Runs the assault dice roll.
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    rs._kill_unit(action.target_id)
                else:
                    rs._kill_unit(action.unit_id)
                    rs._flip_initiative()

                return [(1, rs)]

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        for faction, counter in self._stall_counter.items():
            if counter > _MAX_STALL_LIMIT:
                # mark faction as losing
                if faction == InitiativeState.Faction.BLUE:
                    return InitiativeState.Faction.RED
                elif faction == InitiativeState.Faction.RED:
                    return InitiativeState.Faction.BLUE
        for objective in self._objectives:
            if objective.units_to_destroy == objective.units_destroyed_counter:
                return objective.winning_faction
        return None

    @override
    def deabstract_action(
        self,
        action: WaypointAction,
        gs: GameState,
    ) -> Action:
        match action:
            case WaypointMoveAction():
                return MoveAction(
                    unit_id=action.unit_id,
                    to=self.waypoints[action.move_to_waypoint_id].position,
                )
            case WaypointPivotAction():
                return PivotAction(
                    unit_id=action.unit_id,
                    to=self.waypoints[action.pivot_to_waypoint_id].position,
                )
            case WaypointFireAction():
                return FireAction(
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case WaypointAssaultAction():
                return AssaultAction(
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )

    @override
    def initialize_state(
        self,
        gs: GameState,
    ) -> None:

        # Assemble waypoint-graph game state
        self._initiative = InitiativeSystem.get_initiative(gs)
        self._objectives: list[EliminationObjective] = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )

        # Add grid points as a waypoint
        for point_id, point in enumerate(self._points):
            self.waypoints[point_id] = _WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Add relationships between nodes
        self._add_visibility_relationships(gs)
        self._add_path_relationships()

    def update_state(
        self,
        gs: GameState,
    ) -> None:

        self._initiative = InitiativeSystem.get_initiative(gs)

        if entities := gs.query(AiStallCountComponent):
            _, stall_component = entities[0]
        else:
            gs.add_entity(stall_component := AiStallCountComponent())

        self._stall_counter = deepcopy(stall_component.stall_counter)

        # Add combat units as waypoints and as abstracted units
        new_waypoint_ids: list[int] = []
        for unit_id, transform, combat_unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            # Try to find an existing waypoint at this position
            waypoint_id: int | None = None
            for id, waypoint in self.waypoints.items():
                if waypoint.position == transform.position:
                    waypoint_id = id
                    break

            # If none exists, create a new one
            if waypoint_id is None:
                waypoint_id = len(self.waypoints)
                new_waypoint_ids.append(waypoint_id)

                self.waypoints[waypoint_id] = _WaypointNode(
                    position=transform.position,
                    visible_nodes=set(),
                    movable_paths={},
                )

            # Add the combat unit using the waypoint
            self.combat_units[unit_id] = _AbstractedCombatUnit(
                unit_id=unit_id,
                current_waypoint_id=waypoint_id,
                degrees=transform.degrees,
                status=combat_unit.status,
                faction=combat_unit.faction,
                no_fire=not fire_controls.can_reactive_fire,
            )

        # Update their relationships
        self._add_path_relationships(waypoint_ids_to_update=new_waypoint_ids)
        self._add_visibility_relationships(
            gs=gs,
            waypoint_ids_to_update=new_waypoint_ids,
        )

        # Update their objectives
        self._objectives = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )

    def get_move_interrupts(
        self,
        unit_id: int,
        move_to_id: int | None,
    ) -> list[tuple[int, list[int]]]:
        """Returns a list of (waypoint_id, [enemy_ids]) pair."""
        current_unit = self.combat_units[unit_id]
        current_waypoint = self.waypoints[current_unit.current_waypoint_id]
        interrupt_points: list[tuple[int, list[int]]] = []
        # Same enemy can't reactive fire twice, so need to track
        # Enemies that's already added.
        included_enemy_ids: list[int] = []
        path_waypoint_ids: list[int] = []
        if move_to_id is not None:
            path_waypoint_ids = current_waypoint.movable_paths[move_to_id]
        else:
            path_waypoint_ids = [current_unit.current_waypoint_id]
        for path_waypoint_id in path_waypoint_ids:
            enemy_ids: list[int] = []
            for enemy_id, enemy_unit in self.combat_units.items():
                # Add interrupt if the enemy can reactive fire it
                if enemy_id in included_enemy_ids:
                    continue
                if enemy_unit.faction == current_unit.faction:
                    continue
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    continue
                if enemy_unit.no_fire:
                    continue

                # Firable only if visible
                enemy_waypoint = self.waypoints[enemy_unit.current_waypoint_id]
                enemy_visible_nodes = enemy_waypoint.visible_nodes
                if path_waypoint_id not in enemy_visible_nodes:
                    continue

                path_waypoint = self.waypoints[path_waypoint_id]
                if not LosSystem.in_fov(  # Firable only for within FOV
                    Transform(enemy_waypoint.position, enemy_unit.degrees),
                    path_waypoint.position,
                ):
                    continue

                enemy_ids.append(enemy_id)
                included_enemy_ids.append(enemy_id)
            if enemy_ids != []:
                interrupt_points.append((path_waypoint_id, enemy_ids))
        return interrupt_points

    def _get_reactive_fire_outcomes(
        self,
        interrupts: list[tuple[int, list[int]]],
        unit_id: int,
        move_to_id: int | None,
    ) -> list[tuple[float, "WaypointsState"]]:
        # Get fire permutations for all enemies
        candidate_enemy_ids: list[int] = []
        for _, interrupt_enemies in interrupts:
            candidate_enemy_ids += interrupt_enemies
        permutations = self.get_all_fire_permutations(candidate_enemy_ids)

        # For each permutation, build a new gs outcome
        all_outcomes: list[tuple[float, "WaypointsState"]] = []
        for prob, enemy_fire_outcomes in permutations:
            # Create a new copy; play out the reactive fire and
            # record the gs as a new outcome
            rs = self.copy()
            rs._stall_counter[rs._initiative] = 0
            current_unit = rs.combat_units[unit_id]

            # Track the most-severe fire outcome.
            # More severe outcomes will override this variables.
            reactive_fire_outcome: FireOutcomes | None = None
            for waypoint_id, enemy_ids in interrupts:
                # If the unit got interrupted and stopped moving,
                # subsequent spotters don't get to fire.
                if reactive_fire_outcome is not None:
                    break

                for enemy_id in enemy_ids:
                    # Some previous fire outcomes might have killed unit,
                    # so break early to prevent a non-existant entity being used.
                    if unit_id not in rs.combat_units:
                        break

                    fire_outcome = enemy_fire_outcomes[enemy_id]
                    match fire_outcome:
                        case FireOutcomes.MISS:
                            enemy_unit = rs.combat_units[enemy_id]
                            enemy_unit.no_fire = True
                        case FireOutcomes.PIN:
                            if current_unit.status == CombatUnit.Status.ACTIVE:
                                current_unit.status = CombatUnit.Status.PINNED
                                current_unit.current_waypoint_id = waypoint_id
                                reactive_fire_outcome = fire_outcome
                        case FireOutcomes.SUPPRESS:
                            if current_unit.status != CombatUnit.Status.SUPPRESSED:
                                current_unit.status = CombatUnit.Status.SUPPRESSED
                                current_unit.current_waypoint_id = waypoint_id
                                reactive_fire_outcome = fire_outcome
                            else:
                                rs._kill_unit(unit_id)
                                reactive_fire_outcome = fire_outcome
                        case FireOutcomes.KILL:
                            rs._kill_unit(unit_id)
                            reactive_fire_outcome = FireOutcomes.KILL

            if reactive_fire_outcome in [
                FireOutcomes.SUPPRESS,
                FireOutcomes.KILL,
            ]:
                rs._flip_initiative()

            # Move to destination if no reactive fire
            # Note: pivot action doesn't have move_to_id
            if reactive_fire_outcome is None and move_to_id is not None:
                current_unit.current_waypoint_id = move_to_id

            all_outcomes.append((prob, rs))

        return all_outcomes

    def _pivot_towards(self, unit_id: int, waypoint_id: int) -> None:
        current_unit = self.combat_units[unit_id]
        current_waypoint = self.waypoints[current_unit.current_waypoint_id]
        pivot_waypoint = self.waypoints[waypoint_id]
        pivot_direction = (
            pivot_waypoint.position - current_waypoint.position
        ).normalized()
        angle_rad = math.atan2(pivot_direction.y, pivot_direction.x)
        current_unit.degrees = math.degrees(angle_rad)

    def _flip_initiative(self) -> None:
        match self._initiative:
            case InitiativeState.Faction.BLUE:
                self._initiative = InitiativeState.Faction.RED
            case InitiativeState.Faction.RED:
                self._initiative = InitiativeState.Faction.BLUE

    def _kill_unit(self, unit_id: int) -> None:
        killed_unit = self.combat_units[unit_id]
        self.combat_units.pop(unit_id)
        for objective in self._objectives:
            if killed_unit.faction == objective.target_faction:
                objective.units_destroyed_counter += 1

    def _add_path_relationships(
        self,
        waypoint_ids_to_update: list[int] | Literal["all"] = "all",
    ) -> None:
        waypoints_to_update: list[tuple[int, _WaypointNode]] = []
        if waypoint_ids_to_update == "all":
            waypoints_to_update = list(self.waypoints.items())
        else:
            waypoints_to_update = list(
                [(id, self.waypoints[id]) for id in waypoint_ids_to_update]
            )

        for waypoint_id, waypoint in waypoints_to_update:
            for move_id, move_waypoint in self.waypoints.items():
                move_from = waypoint.position
                move_to = move_waypoint.position
                move_distance = (move_to - move_from).length()
                direction = (move_to - move_from).normalized()

                # Define a set of nodes that forms the best path for this move
                path: list[tuple[int, float]] = []
                for path_id, path_waypoint in self.waypoints.items():
                    t = (path_waypoint.position - move_from).dot(direction)
                    if path_id in [waypoint_id, move_id]:
                        path.append((path_id, t))
                        continue
                    if t < 0:
                        continue
                    if t > move_distance:
                        continue
                    distance_to_line = (
                        (path_waypoint.position - move_from) - (direction * t)
                    ).length()
                    if distance_to_line > self._path_tolerance:
                        continue
                    path.append((path_id, t))

                def sort_key(node_entry: tuple[int, float]) -> float:
                    _, t = node_entry
                    return t

                waypoint.movable_paths[move_id] = list(
                    [id for id, _ in sorted(path, key=sort_key)]
                )

    def _add_visibility_relationships(
        self,
        gs: GameState,
        waypoint_ids_to_update: list[int] | Literal["all"] = "all",
    ) -> None:
        waypoints_to_update: list[tuple[int, _WaypointNode]] = []
        if waypoint_ids_to_update == "all":
            waypoints_to_update = list(self.waypoints.items())
        else:
            waypoints_to_update = list(
                [(id, self.waypoints[id]) for id in waypoint_ids_to_update]
            )

        # Compute LOS polygon for all these waypoints.
        # The LOS polygon might be overkill for now,
        # but future cases might need it
        waypoint_LOS_polygons: dict[int, list[Vec2]] = {}
        for waypoint_id, waypoint in waypoints_to_update:
            waypoint_LOS_polygons[waypoint_id] = LosSystem.get_los_polygon(
                gs, waypoint.position
            )

        # Add visibility relationships between nodes
        for waypoint_id, waypoint in waypoints_to_update:
            for other_id, other_waypoint in self.waypoints.items():
                # Add visibility relationship
                if IntersectGetter.is_inside(
                    other_waypoint.position, waypoint_LOS_polygons[waypoint_id]
                ):
                    waypoint.visible_nodes.add(other_id)
                    other_waypoint.visible_nodes.add(waypoint_id)
