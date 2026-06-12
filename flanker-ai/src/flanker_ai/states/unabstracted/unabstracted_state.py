from copy import deepcopy
from typing import Sequence, override

from flanker_ai.actions import Action
from flanker_ai.config_models import PointsConfig
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.common.ai_action_service import AiActionService
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


class UnabstractedState(IRepresentationState[Action]):
    def __init__(
        self,
        gs: GameState,
        move_candidates_config: PointsConfig,
        divide_moves_per_unit: bool,
    ) -> None:
        self._gs = gs
        self._move_candidates_config = move_candidates_config
        self.move_candidates: list[Vec2] = []
        self._divide_moves_per_unit = divide_moves_per_unit

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for _, combat_unit in self._gs.query(CombatUnit):
            value = 0
            match combat_unit.status:
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
            move_candidates=self.move_candidates,
            divide_moves_per_unit=self._divide_moves_per_unit,
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
            new_state = UnabstractedState(
                gs=branch,
                move_candidates_config=self._move_candidates_config,
                divide_moves_per_unit=self._divide_moves_per_unit,
            )
            new_state.move_candidates = self.move_candidates
            state_branches.append((prob, new_state))
        return state_branches

    @override
    def get_one_branch(
        self,
        action: Action,
    ) -> IRepresentationState[Action] | None:
        branches = AiBranchingService.get_action_branches(self._gs, action)
        if branches == []:
            return None
        branch = AiBranchAbstractionService.pick_branch(branches, action)
        new_state = UnabstractedState(
            gs=branch,
            move_candidates_config=self._move_candidates_config,
            divide_moves_per_unit=self._divide_moves_per_unit,
        )
        new_state.move_candidates = self.move_candidates
        return new_state

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        objective_system = self._gs.get(ObjectiveSystem)
        return objective_system.get_winning_faction(self._gs)

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        initiative_system = self._gs.get(InitiativeSystem)
        return self._gs.get(initiative_system).get_initiative(self._gs)

    def update_state(self, gs: GameState) -> None:
        self._gs = deepcopy(gs)
        # Regenerate the move candidate for each update
        self.move_candidates = AiPointsExpansionService.get_points(
            self._gs, self._move_candidates_config
        )
