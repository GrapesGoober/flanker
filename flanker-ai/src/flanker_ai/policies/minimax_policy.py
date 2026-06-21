from itertools import count
from math import inf

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.components import InitiativeState

MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class MinimaxPolicy[TAction](IPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, int]:
        counter = count()
        _, action = self._search(
            rs=rs,
            depth=self._depth,
            alpha=-inf,
            beta=inf,
            counter=counter,
        )
        return action, next(counter) - 1

    def _search(
        self,
        rs: IRepresentationState[TAction],
        depth: int,
        alpha: float,
        beta: float,
        counter: "count[int]",
    ) -> tuple[float, TAction | None]:

        next(counter)

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
            branch = rs.get_one_branch(action)
            if branch == None:
                continue
            score, _ = self._search(
                rs=branch,
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                counter=counter,
            )

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
