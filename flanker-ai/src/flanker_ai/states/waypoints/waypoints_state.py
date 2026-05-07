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
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointGraphSystem
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
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.systems.register_systems import register_systems

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
        self, points: list[Vec2], path_tolerance: float, is_deterministic: bool
    ) -> None:
        self.gs = GameState()
        register_systems(self.gs)
        self._points = points
        self._path_tolerance = path_tolerance
        self._is_deterministic = is_deterministic

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
            is_deterministic=self._is_deterministic,
        )
        new_gs.gs = self.gs.selective_copy(list(entities_to_copy))
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
        waypoints_system = self.gs.get(WaypointGraphSystem)

        actions: list[Action] = []
        waypoints = waypoints_system.get_waypoints(self.gs)

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
            friendly_waypoint_id = waypoints_system.get_waypoint_id(
                gs=self.gs,
                position=friendly_transform.position,
            )
            friendly_waypoint = waypoints[friendly_waypoint_id]

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
                enemy_waypoint_id = waypoints_system.get_waypoint_id(
                    gs=self.gs,
                    position=enemy_transform.position,
                )
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
                waypoints_system.get_waypoint_id(self.gs, transform.position)
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
                move_position = waypoints[move_to_id].position
                actions.append(
                    MoveAction(
                        unit_id=friendly_id,
                        to=move_position,
                    )
                )

        return actions

    def get_one_fire_outcome(
        self,
        enemy_ids: set[UUID],
    ) -> dict[UUID, FireOutcomes]:
        """Returns a single most-likely fire outcome given enemy units."""
        if len(enemy_ids) == 1:
            all_pins = {enemy_id: FireOutcomes.PIN for enemy_id in enemy_ids}
            return all_pins
        # It should avoid being pinned by more than one enemy
        # by assuming it gets suppressed
        if len(enemy_ids) > 1:
            one_pin = {enemy_id: FireOutcomes.SUPPRESS for enemy_id in enemy_ids}
            one_pin[next(iter(enemy_ids))] = FireOutcomes.PIN
            return one_pin
        return {}

    def get_all_fire_outcomes(
        self, enemy_ids: set[UUID]
    ) -> list[tuple[float, dict[UUID, FireOutcomes]]]:
        """Returns all probabilites and fire outcomes given enemy units."""
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

        match action:
            case MoveAction():
                move_system = self.gs.get(MoveSystem)

                candidates = move_system.get_interrupt_candidates(
                    gs=self.gs, unit_id=action.unit_id, to=action.to
                )
                enemy_ids = {uid for _, uuid_list in candidates for uid in uuid_list}
                if len(enemy_ids) == 0:
                    rs = self.copy()
                    result = move_system.move(rs.gs, action.unit_id, action.to)
                    if isinstance(result, InvalidAction):
                        return []
                    rs._count_stall(count="up")
                    return [(1, rs)]

                if self._is_deterministic:
                    permutations = [(1, self.get_one_fire_outcome(enemy_ids))]
                else:
                    permutations = self.get_all_fire_outcomes(enemy_ids)

                outcomes: list[tuple[float, "WaypointsState"]] = []
                for probability, unit_fire_outcomes in permutations:
                    rs = self.copy()
                    rs._count_stall(count="reset")

                    for firer_id, firer_outcome in unit_fire_outcomes.items():
                        fire_controls = rs.gs.get_component(firer_id, FireControls)
                        fire_controls.override = firer_outcome

                    result = move_system.move(rs.gs, action.unit_id, action.to)
                    if isinstance(result, InvalidAction):
                        # Invalid action won't be performable.
                        return []
                    outcomes.append((probability, rs))
                return outcomes

            case PivotAction():
                rs = self.copy()
                # Perform pivot action to the target position
                move_system = rs.gs.get(MoveSystem)
                for _, fire_controls in rs.gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = move_system.pivot(rs.gs, action.unit_id, action.to)
                if isinstance(result, InvalidAction):
                    return []

                # Count stall depending on results
                combat_unit = rs.gs.get_component(action.unit_id, CombatUnit)
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    rs._count_stall(count="up")
                else:
                    rs._count_stall(count="reset")
                return [(1, rs)]

            case FireAction():
                rs = self.copy()
                rs._count_stall(count="reset")
                fire_controls = rs.gs.get_component(action.unit_id, FireControls)
                # Assumes deterministic suppressive fire
                fire_controls.override = FireOutcomes.SUPPRESS
                fire_system = rs.gs.get(FireSystem)
                result = fire_system.fire(rs.gs, action.unit_id, action.target_id)
                if isinstance(result, InvalidAction):
                    return []
                return [(1, rs)]

            case AssaultAction():
                rs = self.copy()
                rs._count_stall(count="reset")
                # Perform move action to the destination position
                assault_system = rs.gs.get(AssaultSystem)
                for _, fire_controls in rs.gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN

                assault_controls = rs.gs.get_component(action.unit_id, AssaultControls)
                assault_controls.override = AssaultOutcomes.SUCCESS
                result = assault_system.assault(rs.gs, action.unit_id, action.target_id)
                if isinstance(result, InvalidAction):
                    return []
                return [(1, rs)]

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

        self.gs = deepcopy(gs)

        self.gs.replace(
            existing=ObjectiveSystem,
            replacement=AiObjectiveSystem,
        )
        self.gs.replace(
            existing=LosSystem,
            replacement=WaypointsLosSystem,
        )
        self.gs.register(WaypointGraphSystem)

        if self.gs.query(AiStallCountComponent) == []:
            self.gs.add_entity(AiStallCountComponent())

        waypoints_system = self.gs.get(WaypointGraphSystem)

        # Add the waypoints graph, with combat units as new waypoints
        points: list[Vec2] = list(self._points)
        for _, transform, _ in self.gs.query(Transform, CombatUnit):
            # Add new waypoints for each combat units
            if transform.position not in points:
                points.append(transform.position)

        waypoints_system.set_waypoints(
            gs=self.gs,
            points=points,
            path_tolerance=self._path_tolerance,
        )

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
