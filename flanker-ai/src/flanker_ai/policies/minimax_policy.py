from math import inf
from typing import Sequence

from flanker_ai.i_ai_policy import IAiPolicy
from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class MinimaxPolicy[TAction](IAiPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action_sequence(self, gs: IGameState[TAction]) -> Sequence[TAction]:
        _, action = self._search(gs, self._depth, -inf, inf)
        if action is None:
            return []
        return [action]

    def _search(
        self,
        state: IGameState[TAction],
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[float, TAction | None]:

        global count
        if count % 50000 == 0:
            print(count)
        count += 1

        winner = state.get_winner()
        if winner is not None:
            if winner == MAXIMIZING_FACTION:
                return state.get_score(MAXIMIZING_FACTION) + depth, None
            else:
                return state.get_score(MAXIMIZING_FACTION) - depth, None

        if depth == 0:
            return state.get_score(MAXIMIZING_FACTION), None

        actions = state.get_actions()
        if not actions:
            return state.get_score(MAXIMIZING_FACTION), None

        maximizing = state.get_initiative() == MAXIMIZING_FACTION
        best_score = -inf if maximizing else inf
        best_action: TAction | None = None

        for action in actions:
            branch = state.get_deterministic_branch(action)
            if branch is None:
                continue

            score, _ = self._search(branch, depth - 1, alpha, beta)

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_action = action
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_action = action
                beta = min(beta, best_score)

            if beta <= alpha:
                break  # Alpha-beta cutoff

        return best_score, best_action
