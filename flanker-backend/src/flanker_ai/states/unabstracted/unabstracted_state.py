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
from flanker_ai.states.common.ai_points_filter_service import (
    AiPointsFilterService,
)
from flanker_ai.states.common.ai_points_initialize_service import (
    AiPointsInitializeService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


class UnabstractedState(IRepresentationState[Action]):
    def __init__(
        self,
        move_pool_config: PointsConfig.ALL,
        move_filter_config: list[FilterConfig.ALL],
    ) -> None:
        self._gs = GameState()
        self._move_pool_config = move_pool_config
        self._move_filter_config = move_filter_config
        self._move_candidates: list[Vec2] = []

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for unit_id, combat_unit in self._gs.query(CombatUnit):
            value = 0
            match FireSystem.get_status(self._gs, unit_id):
                case CombatUnit.Status.ACTIVE:
                    value = 3
                case CombatUnit.Status.PINNED:
                    value = 2
                case CombatUnit.Status.SUPPRESSED:
                    value = 1

            if combat_unit.faction == maximizing_faction:
                score += value
            else:
                score -= value
        return score

    @override
    def get_actions(self) -> Sequence[Action]:
        return AiActionService.get_actions(
            gs=self._gs,
            initiative=self.get_initiative(),
            move_candidates=self._move_candidates,
        )

    @override
    def get_branches(
        self,
        action: Action,
    ) -> list[tuple[float, "UnabstractedState"]]:
        branches = AiBranchingService.get_action_branches(self._gs, action)
        if branches == []:
            return []
        branches = AiBranchAbstractionService.merge_branches(branches, action)
        # Remove the unlikeliest branch to curb branching factor
        if len(branches) >= 3:
            unlikeliest_branch = min(branches, key=lambda i: i[0])
            branches.remove(unlikeliest_branch)
            leftover_prob, _ = unlikeliest_branch
            prob_to_adjust = leftover_prob / len(branches)
            for i, (prob, branch) in enumerate(branches):
                branches[i] = (prob + prob_to_adjust, branch)

        state_branches: list[tuple[float, UnabstractedState]] = []
        for prob, branch in branches:
            new_state = self.copy(new_gs=branch)
            state_branches.append((prob, new_state))
        return state_branches

    @override
    def perform_action(self, action: Action) -> bool:
        result = ActionSystem.perform(self._gs, action)
        return not isinstance(result, InvalidAction)

    @override
    def copy(
        self,
        new_gs: GameState | None = None,
    ) -> "UnabstractedState":
        if new_gs == None:
            new_gs = AiBranchingService.copy(self._gs)
        new_state = UnabstractedState(
            move_pool_config=self._move_pool_config,
            move_filter_config=self._move_filter_config,
        )
        new_state._move_candidates = self._move_candidates
        new_state._gs = new_gs
        return new_state

    @override
    def get_one_branch(
        self,
        action: Action,
    ) -> IRepresentationState[Action] | None:
        branches = AiBranchingService.get_action_branches(self._gs, action)
        if branches == []:
            return None
        branch = AiBranchAbstractionService.pick_branch(branches, action)
        new_state = self.copy(new_gs=branch)
        return new_state

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        return ObjectiveSystem.get_winning_faction(self._gs)

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        return InitiativeSystem.get_initiative(self._gs)

    @override
    def flip_initiative(self) -> None:
        InitiativeSystem.flip_initiative(self._gs)

    @override
    def update_state(self, gs: GameState) -> None:
        self._gs = deepcopy(gs)
        # Regenerate the move candidates for each update
        initial_move_candidates = AiPointsInitializeService.get_initial_points(
            gs, self._move_pool_config
        )
        self._move_candidates = AiPointsFilterService.filter_points(
            gs=self._gs,
            filter_configs=self._move_filter_config,
            points=initial_move_candidates,
        )

    @override
    def get_hashable_key(self) -> object:
        return AiCacheKeyService.get_key(self._gs)
