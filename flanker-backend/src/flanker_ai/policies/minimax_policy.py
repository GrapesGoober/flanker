from dataclasses import dataclass
from itertools import count
from math import inf
from typing import Any

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.search_log_models import MinimaxSearchLog
from flanker_core.models.components import InitiativeState

MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass(frozen=True)
class _TranspositionCacheKey:
    state_snapshot: Any
    current_depth: int


class MinimaxPolicy[TAction](IPolicy[TAction, MinimaxSearchLog]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, MinimaxSearchLog]:
        counter = count()
        _, action = self._search(
            rs=rs,
            depth=self._depth,
            alpha=-inf,
            beta=inf,
            counter=counter,
            transposition_table={},
        )
        return action, MinimaxSearchLog(
            faction=rs.get_initiative(),
            tree_size=next(counter) - 1,
        )

    def _search(
        self,
        rs: IRepresentationState[TAction],
        depth: int,
        alpha: float,
        beta: float,
        counter: "count[int]",
        transposition_table: dict[object, float],
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

            state_key = branch.get_hashable_key()
            cache_key = _TranspositionCacheKey(
                state_snapshot=state_key,
                current_depth=depth - 1,
            )

            score = transposition_table.get(cache_key, None)
            if score == None:  # Reuse the cached reward if possible
                score, _ = self._search(
                    rs=branch,
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    counter=counter,
                    transposition_table=transposition_table,
                )
                transposition_table[cache_key] = score

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
