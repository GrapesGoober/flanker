import random
from copy import deepcopy
from itertools import product
from math import prod
from typing import Literal, override
from uuid import UUID

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.unabstracted.ai_objective_system import AiObjectiveSystem
from flanker_ai.states.waypoints.models import WaypointNode, WaypointsGraphComponent
from flanker_ai.states.waypoints.waypoints_fire_system import (
    DoublePinAvoidanceConfig,
    WaypointsFireSystem,
)
from flanker_ai.states.waypoints.waypoints_los_system import WaypointsLosSystem
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationObjective,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.systems.register_systems import register_systems
from flanker_core.utils.intersect_getter import IntersectGetter

_FIRE_ACTION_PROBABILITIES = {
    FireOutcomes.PIN: 0.4,
    FireOutcomes.SUPPRESS: 0.6,
}

_FIRE_REACTION_PROBABILITIES = {
    FireOutcomes.PIN: 0.6,
    FireOutcomes.SUPPRESS: 0.4,
}


class WaypointsState(IRepresentationState[Action]):
    def __init__(
        self,
        points: list[Vec2],
        path_tolerance: float,
    ) -> None:
        self.gs = GameState()
        register_systems(self.gs)
        self._points = points
        self._path_tolerance = path_tolerance

    @property
    def waypoints(self) -> dict[int, WaypointNode]:
        if entities := self.gs.query(WaypointsGraphComponent):
            _, component = entities[0]
        else:
            self.gs.add_entity(component := WaypointsGraphComponent({}))
        return component.waypoints

    @waypoints.setter
    def waypoints(self, value: dict[int, WaypointNode]) -> None:
        if entities := self.gs.query(WaypointsGraphComponent):
            _, component = entities[0]
        else:
            self.gs.add_entity(component := WaypointsGraphComponent({}))
        component.waypoints = value

    @override
    def copy(self) -> "WaypointsState":
        entities_to_copy: set[UUID] = set()  # Use set to filter duplicates
        for id, _ in self.gs.query(InitiativeState):
            entities_to_copy.add(id)
        for id, _ in self.gs.query(EliminationObjective):
            entities_to_copy.add(id)
        for id, _ in self.gs.query(CombatUnit):
            entities_to_copy.add(id)
        for id, _ in self.gs.query(AiStallCountComponent):
            entities_to_copy.add(id)

        new_gs = WaypointsState(
            points=self._points,
            path_tolerance=self._path_tolerance,
        )
        new_gs.gs = self.gs.selective_copy(list(entities_to_copy))
        new_gs.waypoints = self.waypoints
        return new_gs

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        initiative_system = self.gs.get(InitiativeSystem)
        return initiative_system.get_initiative(self.gs)

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for _, unit in self.gs.query(CombatUnit):
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
    def get_actions(self) -> list[Action]:

        los_system = self.gs.get(LosSystem)

        actions: list[Action] = []

        # Aggregate a list of friendly and enemy units separately
        # instead of inside the big loop. This keeps time complexity low.
        friendly_ids: list[UUID] = []
        enemy_ids: list[UUID] = []
        for combat_unit_id, combat_unit in self.gs.query(CombatUnit):
            if combat_unit.faction == self.get_initiative():
                friendly_ids.append(combat_unit_id)
            if combat_unit.faction != self.get_initiative():
                enemy_ids.append(combat_unit_id)

        for friendly_id in friendly_ids:
            friendly_transform = self.gs.get_component(friendly_id, Transform)
            friendly_waypoint_id = self._get_waypoint_id(friendly_transform.position)
            friendly_waypoint = self.waypoints[friendly_waypoint_id]

            # Adds assault & fire actions for each friendly-enemy permutation
            for enemy_id in enemy_ids:
                actions.append(
                    FireAction(
                        unit_id=friendly_id,
                        target_id=enemy_id,
                    )
                )
                actions.append(
                    AssaultAction(
                        unit_id=friendly_id,
                        target_id=enemy_id,
                    )
                )

            # Add move and pivot actions.
            # For pivot actions, have it pivot towards enemies only.
            # This is generalized action filter to reduce branching factor.
            for enemy_id in enemy_ids:
                enemy_transform = self.gs.get_component(enemy_id, Transform)
                enemy_waypoint_id = self._get_waypoint_id(enemy_transform.position)
                # if already looking there, no need to pivot again
                if los_system.in_fov(
                    Transform(friendly_waypoint.position, friendly_transform.degrees),
                    enemy_transform.position,
                ):
                    continue
                # If the target isn't in LOS, don't need to pivot.
                if enemy_waypoint_id not in friendly_waypoint.visible_nodes:
                    continue
                actions.append(
                    PivotAction(
                        unit_id=friendly_id,
                        to=enemy_transform.position,
                    )
                )

            # Adds move actions last, for best alpha-beta pruning.
            # Have friendly units move to non-occupied waypoints
            occupied_waypoint_ids: set[int] = {
                self._get_waypoint_id(transform.position)
                for _, _, transform in self.gs.query(CombatUnit, Transform)
            }
            available_waypoints: list[int] = [
                waypoint_id
                for waypoint_id in friendly_waypoint.movable_paths.keys()
                if waypoint_id not in occupied_waypoint_ids
            ]

            # Randomly filter move waypoints to reduce branching factor
            for move_to_id in random.sample(
                population=available_waypoints,
                k=min(9, len(available_waypoints)),
            ):
                move_position = self.waypoints[move_to_id].position
                actions.append(
                    MoveAction(
                        unit_id=friendly_id,
                        to=move_position,
                    )
                )

        return actions

    # TODO: this should be removed. It's duplicate code.
    # Currently the reactive fire uses deterministic outcome.
    # I still want this to handle peeking.
    @override
    def get_deterministic_branch(
        self,
        action: Action,
    ) -> "WaypointsState":

        for _, conf in self.gs.query(DoublePinAvoidanceConfig):
            conf.avoids_double_pins = True

        match action:
            case MoveAction():
                rs = self.copy()

                # Perform move action to the destination position
                move_system = rs.gs.get(MoveSystem)
                for _, fire_controls in rs.gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                move_system.move(rs.gs, action.unit_id, action.to)

                # Skip handling if unit is killed
                combat_unit = rs.gs.try_component(action.unit_id, CombatUnit)
                if combat_unit == None:
                    rs._count_stall(count="reset")
                    return rs

                # Count stall depending on move results
                combat_unit = rs.gs.get_component(action.unit_id, CombatUnit)
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    rs._count_stall(count="up")
                else:
                    rs._count_stall(count="reset")
                return rs

            case PivotAction():
                rs = self.copy()
                # Perform pivot action to the target position
                move_system = rs.gs.get(MoveSystem)
                for _, fire_controls in rs.gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                move_system.pivot(rs.gs, action.unit_id, action.to)

                # Count stall depending on results
                combat_unit = rs.gs.get_component(action.unit_id, CombatUnit)
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    rs._count_stall(count="up")
                else:
                    rs._count_stall(count="reset")
                return rs

            case FireAction():
                rs = self.copy()
                rs._count_stall(count="reset")
                fire_controls = rs.gs.get_component(action.unit_id, FireControls)
                # Assumes deterministic suppressive fire
                fire_controls.override = FireOutcomes.SUPPRESS
                fire_system = rs.gs.get(FireSystem)
                fire_system.fire(rs.gs, action.unit_id, action.target_id)
                return rs

            case AssaultAction():
                rs = self.copy()
                rs._count_stall(count="reset")
                # Perform move action to the destination position
                assault_system = rs.gs.get(AssaultSystem)
                for _, fire_controls in rs.gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN

                assault_controls = rs.gs.get_component(action.unit_id, AssaultControls)
                assault_controls.override = AssaultOutcomes.SUCCESS
                assault_system.assault(rs.gs, action.unit_id, action.target_id)
                return rs

    def get_all_fire_permutations(
        self, enemy_ids: list[UUID]
    ) -> list[tuple[float, dict[UUID, FireOutcomes]]]:
        """Returns all permutations of (unit, outcome) and their probabilities."""
        permutations: list[
            tuple[
                float,  # total probability of this permutation event
                dict[UUID, FireOutcomes],  # event (key=enemy, value=outcome)
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
    def get_branches(self, action: Action) -> list[tuple[float, "WaypointsState"]]:

        for _, conf in self.gs.query(DoublePinAvoidanceConfig):
            conf.avoids_double_pins = False

        match action:

            # NOTE
            # This is just a placeholder implementation
            # to test out how the refactor works

            case MoveAction():
                move_system = self.gs.get(MoveSystem)

                candidates = move_system.get_interrupt_candidates(
                    gs=self.gs, unit_id=action.unit_id, to=action.to
                )
                enemy_ids = list(
                    {uid for _, uuid_list in candidates for uid in uuid_list}
                )
                permutations = self.get_all_fire_permutations(list(enemy_ids))
                outcomes: list[tuple[float, "WaypointsState"]] = []
                for probability, unit_fire_outcomes in permutations:
                    rs = self.copy()

                    for firer_id, firer_outcome in unit_fire_outcomes.items():
                        fire_controls = rs.gs.get_component(firer_id, FireControls)
                        fire_controls.override = firer_outcome

                    move_system.move(rs.gs, action.unit_id, action.to)

                    # Skip handling if unit is killed
                    combat_unit = rs.gs.try_component(action.unit_id, CombatUnit)
                    if combat_unit == None:
                        rs._count_stall(count="reset")
                        continue

                    # Count stall depending on move results
                    combat_unit = rs.gs.get_component(action.unit_id, CombatUnit)
                    if combat_unit.status == CombatUnit.Status.ACTIVE:
                        rs._count_stall(count="up")
                    else:
                        rs._count_stall(count="reset")
                    # Record the outcome
                    outcomes.append((probability, rs))
                return outcomes
            case _:
                raise NotImplementedError()

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        objective_system = self.gs.get(ObjectiveSystem)
        return objective_system.get_winning_faction(self.gs)

    @override
    def deabstract_action(
        self,
        action: Action,
        gs: GameState,
    ) -> Action:
        return action

    @override
    def update_state(
        self,
        gs: GameState,
    ) -> None:

        # The waypoints getter is a game state query, thus the waypoints
        # is gone when game state is copied and reset.
        # NOTE: should there be a better state initialization framework?
        initialized_waypoints = self.waypoints
        self.gs = deepcopy(gs)
        self.waypoints = initialized_waypoints

        self.gs.replace(
            existing=ObjectiveSystem,
            replacement=AiObjectiveSystem,
        )
        self.gs.replace(
            existing=LosSystem,
            replacement=WaypointsLosSystem,
        )
        self.gs.replace(
            existing=FireSystem,
            replacement=WaypointsFireSystem,
        )

        if self.gs.query(DoublePinAvoidanceConfig) == []:
            self.gs.add_entity(DoublePinAvoidanceConfig())

        if self.gs.query(AiStallCountComponent) == []:
            self.gs.add_entity(AiStallCountComponent())

        # Add grid points as a waypoint
        for point_id, point in enumerate(self._points):
            self.waypoints[point_id] = WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Add new waypoints to represent combat units
        for _, transform, _ in self.gs.query(Transform, CombatUnit):
            # Try to find an existing waypoint at this position
            waypoint_id: int | None = None
            for id, waypoint in self.waypoints.items():
                if waypoint.position == transform.position:
                    waypoint_id = id
                    break

            # If waypoint doesn't exist, create a new one
            if waypoint_id is None:
                waypoint_id = len(self.waypoints)
                self.waypoints[waypoint_id] = WaypointNode(
                    position=transform.position,
                    visible_nodes=set(),
                    movable_paths={},
                )

        # Add relationships between nodes
        self._add_visibility_relationships(self.gs)
        self._add_path_relationships()

    def _count_stall(
        self,
        count: Literal["up"] | Literal["reset"],
    ) -> None:

        if entities := self.gs.query(AiStallCountComponent):
            _, stall_component = entities[0]
        else:
            self.gs.add_entity(stall_component := AiStallCountComponent())

        initiative = self.get_initiative()
        match count:
            case "up":
                stall_component.stall_counter[initiative] += 1
            case "reset":
                stall_component.stall_counter[initiative] = 0

    def _get_waypoint_id(self, position: Vec2) -> int:
        coerced_waypoint_id = min(
            self.waypoints.keys(),
            key=lambda idx: abs((position - self.waypoints[idx].position).length()),
        )
        return coerced_waypoint_id

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
        los_system = gs.get(LosSystem)
        for waypoint_id, waypoint in waypoints_to_update:
            waypoint_LOS_polygons[waypoint_id] = los_system.get_los_polygon(
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
