import random
from copy import deepcopy
from itertools import product
from math import prod
from typing import Any, Literal, override
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

    def get_permutations[T](
        self,
        unit_ids: set[UUID],
        outcome_probabilities: dict[T, float],
    ) -> list[tuple[float, dict[UUID, T]]]:
        """Get a list of all event permutations T for each entity ID"""

        permutations: list[
            tuple[
                float,  # total probability of this permutation event
                dict[UUID, T],  # event (key=entity, value=outcome)
            ]
        ] = []

        # Assemble the probability and fire outcomes
        outcomes = list(outcome_probabilities.keys())
        for outcome_combo in product(outcomes, repeat=len(unit_ids)):
            probability = prod(
                outcome_probabilities[outcome] for outcome in outcome_combo
            )
            event = {
                unit_id: outcome for unit_id, outcome in zip(unit_ids, outcome_combo)
            }
            permutations.append((probability, event))
        return permutations

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

    def _get_reactive_fire_branches(
        self,
        unit_id: UUID,
        move_to: Vec2,
    ) -> list[tuple[float, "WaypointsState"]]:
        move_system = self.gs.get(MoveSystem)
        reactive_fire_candidates = move_system.get_interrupt_candidates(
            self.gs, unit_id, move_to
        )
        reactive_fire_ids = {
            uid for _, uuid_list in reactive_fire_candidates for uid in uuid_list
        }

        # No reactive fire found; this is garantee outcome
        if len(reactive_fire_ids) == 0:
            new_state = self.copy()
            new_state._count_stall("up")
            return [(1, new_state)]

        # Reactive fire found; configure all permutations
        permutations: list[tuple[float, dict[UUID, FireOutcomes]]]
        if self._is_deterministic:
            if len(reactive_fire_ids) == 1:
                outcomes = {next(iter(reactive_fire_ids)): FireOutcomes.PIN}
            else:
                # Enforce avoidance by having it assume
                # 2 reactive fires means SUPPRESS, and 3 means KILL
                outcomes = {
                    enemy_id: FireOutcomes.SUPPRESS for enemy_id in reactive_fire_ids
                }
                outcomes[next(iter(reactive_fire_ids))] = FireOutcomes.PIN
            permutations = [(1, outcomes)]
        else:
            permutations = self.get_permutations(
                unit_ids=reactive_fire_ids,
                outcome_probabilities={
                    FireOutcomes.PIN: 0.6,
                    FireOutcomes.SUPPRESS: 0.4,
                },
            )
        if len(permutations) == 0:
            raise Exception("Permutations are empty, something went wrong!")

        # Permutation configured; create branches
        branching_states: list[tuple[float, "WaypointsState"]] = []
        for probability, unit_fire_outcomes in permutations:
            new_state = self.copy()
            new_state._count_stall(count="reset")
            for firer_id, firer_outcome in unit_fire_outcomes.items():
                fire_controls = new_state.gs.get_component(firer_id, FireControls)
                fire_controls.override = firer_outcome
            branching_states.append((probability, new_state))
        return branching_states

    def _get_fire_branches(
        self,
        unit_id: UUID,
    ) -> list[tuple[float, "WaypointsState"]]:
        # Configure this to be deterministic for simplicity for now.
        new_state = self.copy()
        new_state._count_stall(count="reset")
        fire_controls = new_state.gs.get_component(unit_id, FireControls)
        fire_controls.override = FireOutcomes.SUPPRESS
        return [(1, new_state)]

    @override
    def get_branches(self, action: Action) -> list[tuple[float, "WaypointsState"]]:
        move_system = self.gs.get(MoveSystem)
        assault_system = self.gs.get(AssaultSystem)
        fire_system = self.gs.get(FireSystem)

        # Prepare a list of configured branches
        branches: list[tuple[float, WaypointsState]]
        match action:
            case MoveAction():
                branches = self._get_reactive_fire_branches(
                    unit_id=action.unit_id, move_to=action.to
                )
            case PivotAction():
                transform = self.gs.get_component(action.unit_id, Transform)
                branches = self._get_reactive_fire_branches(
                    unit_id=action.unit_id, move_to=transform.position
                )
            case AssaultAction():
                transform = self.gs.get_component(action.target_id, Transform)
                branches = self._get_reactive_fire_branches(
                    unit_id=action.unit_id, move_to=transform.position
                )
                for _, new_state in branches:
                    assault_controls = self.gs.get_component(
                        action.unit_id, AssaultControls
                    )
                    assault_controls.override = AssaultOutcomes.SUCCESS
            case FireAction():
                branches = self._get_fire_branches(action.unit_id)

        # Perform the actions
        for _, new_state in branches:
            result: Any | InvalidAction
            match action:
                case MoveAction():
                    result = move_system.move(
                        gs=new_state.gs,
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case PivotAction():
                    result = move_system.pivot(
                        gs=new_state.gs,
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case AssaultAction():
                    result = assault_system.assault(
                        gs=new_state.gs,
                        attacker_id=action.unit_id,
                        target_id=action.target_id,
                    )
                case FireAction():
                    result = fire_system.fire(
                        gs=new_state.gs,
                        attacker_id=action.unit_id,
                        target_id=action.target_id,
                    )

            # Invalid action won't be performable.
            if isinstance(result, InvalidAction):
                return []

        return branches

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
