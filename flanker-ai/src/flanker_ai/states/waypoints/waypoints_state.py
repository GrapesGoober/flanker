import random
from copy import deepcopy
from typing import override
from uuid import UUID

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointsGraphSystem
from flanker_ai.states.waypoints.waypoints_los_system import WaypointsLosSystemOverrides
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import (
    GetLosFromLineOverrideComponent,
    HasLosOverrideComponent,
    LosSystem,
)
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.systems.register_systems import register_systems


class WaypointsState(IRepresentationState[Action]):
    def __init__(self, points: list[Vec2], path_tolerance: float) -> None:
        self.gs = GameState()
        register_systems(self.gs)
        self._points = points
        self._path_tolerance = path_tolerance

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        return InitiativeSystem.get_initiative(self.gs)

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for unit_id, unit in self.gs.query(CombatUnit):
            value = 0
            match FireSystem.get_status(self.gs, unit_id):
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
        waypoints_system = self.gs.get(WaypointsGraphSystem)

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

    @override
    def get_branches(self, action: Action) -> list[tuple[float, "WaypointsState"]]:
        branches = AiBranchingService.get_action_branches(self.gs, action)
        state_branches: list[tuple[float, WaypointsState]] = []
        for probability, new_state in branches:
            new_waypoints_state = WaypointsState(
                points=self._points,
                path_tolerance=self._path_tolerance,
            )
            new_waypoints_state.gs = new_state
            state_branches.append((probability, new_waypoints_state))
        return state_branches

    @override
    def get_one_branch(self, action: Action) -> "WaypointsState | None":
        branches = AiBranchingService.get_action_branches(self.gs, action)
        if branches == []:
            return None
        branch = AiBranchAbstractionService.pick_branch(branches, action)
        new_waypoints_state = WaypointsState(
            points=self._points,
            path_tolerance=self._path_tolerance,
        )
        new_waypoints_state.gs = branch
        return new_waypoints_state

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        return ObjectiveSystem.get_winning_faction(self.gs)

    @override
    def update_state(
        self,
        gs: GameState,
    ) -> None:

        self.gs = deepcopy(gs)
        self.gs.add_entity(
            GetLosFromLineOverrideComponent(
                method=WaypointsLosSystemOverrides.get_los_from_line,
            ),
            HasLosOverrideComponent(
                method=WaypointsLosSystemOverrides.has_los,
            ),
        )

        self.gs.register(WaypointsGraphSystem)

        waypoints_system = self.gs.get(WaypointsGraphSystem)

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
