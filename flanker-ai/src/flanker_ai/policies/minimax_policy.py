from math import inf
from typing import Sequence

from flanker_ai.i_ai_policy import IAiPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class MinimaxPolicy[TAction](IAiPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action_sequence(self, rs: IRepresentationState[TAction]) -> Sequence[TAction]:
        _, action = self._search(rs, self._depth, -inf, inf)
        if action is None:
            return []
        return [action]

    def _search(
        self,
        rs: IRepresentationState[TAction],
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[float, TAction | None]:

        global count
        if count % 50000 == 0:
            print(count)
        count += 1

        winner = rs.get_winner()
        if winner is not None:
            if winner == MAXIMIZING_FACTION:
                return rs.get_score(MAXIMIZING_FACTION) + depth, None
            else:
                return rs.get_score(MAXIMIZING_FACTION) - depth, None

        if depth == 0:
            return rs.get_score(MAXIMIZING_FACTION), None

        actions = rs.get_actions()
        if not actions:
            return rs.get_score(MAXIMIZING_FACTION), None

        maximizing = rs.get_initiative() == MAXIMIZING_FACTION
        best_score = -inf if maximizing else inf
        best_action: TAction | None = None

        for action in actions:
            branch = rs.get_deterministic_branch(action)
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
