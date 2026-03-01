import random
from dataclasses import dataclass, replace
from typing import Literal, override

from flanker_ai.i_game_state import IGameState
from flanker_ai.actions import Action, AssaultAction, FireAction, MoveAction
from flanker_ai.waypoints.models import (
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
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


@dataclass
class AbstractedCombatUnit:
    # Note: this should be kept flat to be serializable
    unit_id: int
    current_waypoint_id: int
    status: CombatUnit.Status
    faction: InitiativeState.Faction
    no_fire: bool


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


class WaypointsGameState(IGameState[WaypointAction]):
    def __init__(
        self,
        points: list[Vec2],
        path_tolerance: float,
    ) -> None:
        self.points = points
        self.waypoints: dict[int, WaypointNode] = {}
        self.combat_units: dict[int, AbstractedCombatUnit] = {}
        self.initiative: InitiativeState.Faction = InitiativeState.Faction.BLUE
        self.objectives: list[EliminationObjective] = []
        self.path_tolerance = path_tolerance

    @override
    def copy(self) -> "WaypointsGameState":
        copied_units = {id: replace(unit) for id, unit in self.combat_units.items()}
        copied_objectives = [replace(obj) for obj in self.objectives]
        new_gs = WaypointsGameState(
            points=self.points,
            path_tolerance=self.path_tolerance,
        )
        new_gs.waypoints = self.waypoints
        new_gs.combat_units = copied_units
        new_gs.initiative = self.initiative
        new_gs.objectives = copied_objectives
        return new_gs

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        return self.initiative

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
        friendly_units: list[tuple[int, AbstractedCombatUnit]] = []
        enemy_units: list[tuple[int, AbstractedCombatUnit]] = []
        for combat_unit_id, combat_unit in self.combat_units.items():
            if combat_unit.faction == self.initiative:
                friendly_units.append((combat_unit_id, combat_unit))
            if combat_unit.faction != self.initiative:
                enemy_units.append((combat_unit_id, combat_unit))

        for combat_unit_id, combat_unit in friendly_units:
            current_waypoint = self.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != self.initiative:
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
                    interrupt = self._get_move_interrupt(
                        combat_unit, enemy_unit.current_waypoint_id
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
                    k=9,
                )

                for move_to_id in movable_nodes:
                    interrupt = self._get_move_interrupt(
                        combat_unit,
                        move_to_id,
                    )
                    actions.append(
                        WaypointMoveAction(
                            unit_id=combat_unit_id,
                            move_to_waypoint_id=move_to_id,
                            interrupt_at_id=interrupt,
                        )
                    )

        return actions

    # TODO: this should be removed. It's only useful for normal MCTS.
    # The deterministic policies could simple choose the most likely
    # option from the probability distribution
    @override
    def get_deterministic_branch(
        self,
        action: WaypointAction,
    ) -> "WaypointsGameState":

        match action:
            case WaypointMoveAction():
                gs = self.copy()
                current_unit = gs.combat_units[action.unit_id]
                # Check for move interrupts
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now
                    current_unit.status = CombatUnit.Status.PINNED
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                return gs

            case WaypointFireAction():
                gs = self.copy()
                # Assumes determinic for now
                target_unit = gs.combat_units[action.target_id]
                target_unit.status = CombatUnit.Status.SUPPRESSED
                return gs

            case WaypointAssaultAction():
                gs = self.copy()
                # Check for move interrupts
                current_unit = gs.combat_units[action.unit_id]
                target_unit = gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    gs._flip_initiative()
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = target_unit.current_waypoint_id

                # Runs the assault dice roll. Assumes determinic for now
                killed_unit: AbstractedCombatUnit
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    gs.combat_units.pop(action.target_id)
                    killed_unit = target_unit
                else:
                    killed_unit = current_unit
                    gs.combat_units.pop(action.unit_id)
                    # Assault failed
                    gs._flip_initiative()

                for objective in gs.objectives:
                    if killed_unit.faction == objective.target_faction:
                        objective.units_destroyed_counter += 1
                return gs

    @override
    def get_branches(
        self, action: WaypointAction
    ) -> list[tuple[float, "WaypointsGameState"]]:
        match action:
            case WaypointMoveAction():
                # Check for move interrupts
                if action.interrupt_at_id is not None:
                    outcomes: list[tuple[float, "WaypointsGameState"]] = []
                    for outcome, probability in _FIRE_REACTION_PROBABILITIES.items():
                        gs = self.copy()
                        current_unit = gs.combat_units[action.unit_id]
                        match outcome:
                            case FireOutcomes.MISS:
                                current_unit.current_waypoint_id = (
                                    action.move_to_waypoint_id
                                )
                            case FireOutcomes.PIN:
                                current_unit.status = CombatUnit.Status.PINNED
                                current_unit.current_waypoint_id = (
                                    action.interrupt_at_id
                                )
                            case FireOutcomes.SUPPRESS:
                                current_unit.status = CombatUnit.Status.SUPPRESSED
                                gs._flip_initiative()
                            case FireOutcomes.KILL:
                                gs._kill_unit(action.unit_id)
                                gs._flip_initiative()

                        outcomes.append((probability, gs))
                    return outcomes
                else:
                    gs = self.copy()
                    current_unit = gs.combat_units[action.unit_id]
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                    return [(1, gs)]

            case WaypointFireAction():
                outcomes: list[tuple[float, "WaypointsGameState"]] = []
                for outcome, probability in _FIRE_ACTION_PROBABILITIES.items():
                    gs = self.copy()
                    target_unit = gs.combat_units[action.target_id]
                    match outcome:
                        case FireOutcomes.MISS:
                            gs._flip_initiative()
                        case FireOutcomes.PIN:
                            if target_unit.status == CombatUnit.Status.ACTIVE:
                                target_unit.status = CombatUnit.Status.PINNED
                            gs._flip_initiative()
                        case FireOutcomes.SUPPRESS:
                            target_unit.status = CombatUnit.Status.SUPPRESSED
                        case FireOutcomes.KILL:
                            gs._kill_unit(action.target_id)
                    outcomes.append((probability, gs))

                return outcomes

            case WaypointAssaultAction():  # Assumes determinic for now
                gs = self.copy()
                # Check for move interrupts
                current_unit = gs.combat_units[action.unit_id]
                target_unit = gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    gs._flip_initiative()
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = target_unit.current_waypoint_id

                # Runs the assault dice roll.
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    gs._kill_unit(action.target_id)
                else:
                    gs._kill_unit(action.unit_id)
                    gs._flip_initiative()

                return [(1, gs)]

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        for objective in self.objectives:
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
        self.initiative = InitiativeSystem.get_initiative(gs)
        self.objectives: list[EliminationObjective] = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )

        # Add grid points as a waypoint
        for point_id, point in enumerate(self.points):
            self.waypoints[point_id] = WaypointNode(
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

        self.initiative = InitiativeSystem.get_initiative(gs)

        # Add combat units as waypoints and as abstracted units
        new_waypoint_ids: list[int] = []
        for unit_id, transform, combat_unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            waypoint_id = len(self.waypoints.keys())
            new_waypoint_ids.append(waypoint_id)
            self.waypoints[waypoint_id] = WaypointNode(
                position=transform.position,
                visible_nodes=set(),
                movable_paths={},
            )
            self.combat_units[unit_id] = AbstractedCombatUnit(
                unit_id=unit_id,
                current_waypoint_id=waypoint_id,
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
        self.objectives = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )

    def _get_move_interrupt(
        self,
        current_unit: AbstractedCombatUnit,
        move_to_id: int,
    ) -> int | None:
        current_waypoint = self.waypoints[current_unit.current_waypoint_id]
        for path_id in current_waypoint.movable_paths[move_to_id]:
            for enemy_unit in self.combat_units.values():
                # Add interrupt if the enemy can reactive fire it
                if enemy_unit.faction == current_unit.faction:
                    continue
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    continue
                enemy_visible_nodes = self.waypoints[
                    enemy_unit.current_waypoint_id
                ].visible_nodes
                if path_id in enemy_visible_nodes:
                    return path_id
        return None

    def _flip_initiative(self) -> None:
        match self.initiative:
            case InitiativeState.Faction.BLUE:
                self.initiative = InitiativeState.Faction.RED
            case InitiativeState.Faction.RED:
                self.initiative = InitiativeState.Faction.BLUE

    def _kill_unit(self, unit_id: int) -> None:
        killed_unit = self.combat_units[unit_id]
        self.combat_units.pop(unit_id)
        for objective in self.objectives:
            if killed_unit.faction == objective.target_faction:
                objective.units_destroyed_counter += 1

    def _add_path_relationships(
        self,
        waypoint_ids_to_update: list[int] | Literal["all"] = "all",
    ) -> None:
        waypoints_to_update: list[tuple[int, WaypointNode]] = []
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
                    if distance_to_line > self.path_tolerance:
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
        waypoints_to_update: list[tuple[int, WaypointNode]] = []
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
