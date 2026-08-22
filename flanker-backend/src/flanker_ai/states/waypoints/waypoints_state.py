from copy import deepcopy
from typing import Sequence, override

from flanker_ai.config_models import (
    FilterConfig,
    PointsConfig,
)
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.common.ai_action_service import AiActionService
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
from flanker_ai.states.common.ai_cache_key_service import AiCacheKeyService
from flanker_ai.states.common.ai_points_filter_service import AiPointsFilterService
from flanker_ai.states.common.ai_points_initialize_service import (
    AiPointsInitializeService,
)
from flanker_ai.states.waypoints.waypoints_graph import WaypointsGraph
from flanker_ai.states.waypoints.waypoints_los_system_overrides import (
    WaypointsLosSystemOverrides,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from flanker_core.models.components import CombatUnit, InitiativeState, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystemOverrides
from flanker_core.systems.objective_system import ObjectiveSystem


class WaypointsState(IRepresentationState[Action]):
    def __init__(
        self,
        waypoints_config: PointsConfig.ALL,
        move_filter_config: list[FilterConfig.ALL],
        path_tolerance: float,
    ) -> None:
        self.gs = GameState()
        self._waypoints_config = waypoints_config
        self._move_filter_config = move_filter_config
        # Can't initialize waypoints without a game state
        self._waypoints = []
        self._move_candidates = []
        self._path_tolerance = path_tolerance

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        return InitiativeSystem.get_initiative(self.gs)

    @override
    def flip_initiative(self) -> None:
        InitiativeSystem.flip_initiative(self.gs)

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
    def perform_action(self, action: Action) -> bool:
        result = ActionSystem.perform(self.gs, action)
        return not isinstance(result, InvalidAction)

    @override
    def copy(self) -> "WaypointsState":
        new_waypoints_state = WaypointsState(
            waypoints_config=self._waypoints_config,
            move_filter_config=self._move_filter_config,
            path_tolerance=self._path_tolerance,
        )
        new_waypoints_state.gs = AiBranchingService.copy(self.gs)
        return new_waypoints_state

    @override
    def get_actions(self) -> Sequence[Action]:

        return AiActionService.get_actions(
            gs=self.gs,
            initiative=InitiativeSystem.get_initiative(self.gs),
            move_candidates=self._move_candidates,
            divide_moves_per_unit=False,
        )

    @override
    def get_branches(self, action: Action) -> list[tuple[float, "WaypointsState"]]:
        branches = AiBranchingService.get_action_branches(self.gs, action)
        state_branches: list[tuple[float, WaypointsState]] = []
        for probability, new_state in branches:
            new_waypoints_state = WaypointsState(
                waypoints_config=self._waypoints_config,
                move_filter_config=self._move_filter_config,
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
            waypoints_config=self._waypoints_config,
            move_filter_config=self._move_filter_config,
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
            LosSystemOverrides.GetLosFromLine(
                method=WaypointsLosSystemOverrides.get_los_from_line,
            ),
            LosSystemOverrides.HasLos(
                method=WaypointsLosSystemOverrides.has_los,
            ),
        )

        self._waypoints = AiPointsInitializeService.get_initial_points(
            self.gs, self._waypoints_config
        )

        # Consider a new list with combat units positions
        points: list[Vec2] = list(self._waypoints)
        for _, transform, _ in self.gs.query(Transform, CombatUnit):
            if transform.position not in points:
                points.append(transform.position)

        occupied_waypoints = {
            transform.position
            for _, _, transform in self.gs.query(CombatUnit, Transform)
        }
        self._move_candidates = [
            move_candidate
            for move_candidate in AiPointsFilterService.filter_points(
                self.gs, self._move_filter_config, self._waypoints
            )
            if move_candidate not in occupied_waypoints
        ]

        WaypointsGraph.set_waypoints(
            gs=self.gs,
            points=points,
            path_tolerance=self._path_tolerance,
        )

    @override
    def get_hashable_key(self) -> object:
        return AiCacheKeyService.get_key(self.gs)
