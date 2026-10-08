from dataclasses import dataclass
from itertools import count
from math import inf

from flanker_ai.search_states.i_search_state import ISearchState
from flanker_core.models.components import InitiativeState

MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass
class _TranspositionEntry:
    score: float
    depth_remaining: int


@dataclass
class MinimaxSearchLog:
    tree_size: int


class MinimaxPolicy[TAction]:

    @staticmethod
    def get_action(
        rs: ISearchState[TAction],
        depth: int,
    ) -> tuple[TAction | None, MinimaxSearchLog]:
        counter = count()
        _, action = MinimaxPolicy[TAction]._search(
            rs=rs,
            depth_remaining=depth,
            alpha=-inf,
            beta=inf,
            counter=counter,
            transposition_table={},
        )
        return action, MinimaxSearchLog(
            tree_size=next(counter) - 1,
        )

    @staticmethod
    def _search(
        rs: ISearchState[TAction],
        depth_remaining: int,
        alpha: float,
        beta: float,
        counter: "count[int]",
        transposition_table: dict[object, _TranspositionEntry],
    ) -> tuple[float, TAction | None]:

        next(counter)

        # Have early return for terminal states and leaf nodes.
        winner = rs.get_winner()
        if winner is not None:
            if winner == MAXIMIZING_FACTION:
                return rs.get_score(MAXIMIZING_FACTION), None
            else:
                return rs.get_score(MAXIMIZING_FACTION), None
        if depth_remaining == 0:
            return rs.get_score(MAXIMIZING_FACTION), None

        # If no legal actions are possible, then consider it as lost
        actions = rs.get_actions()
        if not actions:
            return rs.get_score(MAXIMIZING_FACTION), None

        # Loop through each action and recursively expand tree
        maximizing = rs.get_initiative() == MAXIMIZING_FACTION
        best_score = -inf if maximizing else inf
        best_action: TAction | None = None
        for action in actions:
            branch = rs.get_one_branch(action)
            if branch == None:
                continue

            new_branch_depth = depth_remaining - 1
            state_key = branch.get_hashable_key()
            cached_entry = transposition_table.get(state_key)

            # Reuse the cached score value if exist, but also only if the
            # cached entry is shallower than the current ply.
            if (
                cached_entry is not None
                and cached_entry.depth_remaining >= new_branch_depth
            ):
                score = cached_entry.score
            else:
                score, _ = MinimaxPolicy[TAction]._search(
                    rs=branch,
                    depth_remaining=new_branch_depth,
                    alpha=alpha,
                    beta=beta,
                    counter=counter,
                    transposition_table=transposition_table,
                )
                # Have scores be closer to zero the further down the tree.
                # This numbs the impact of future gains or future losses.
                # Ex: future wins is less preferable than closer wins.
                score = score * 0.9

                transposition_table[state_key] = _TranspositionEntry(
                    score=score,
                    depth_remaining=new_branch_depth,
                )

            # Handle alpha-beta pruning
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
                break  # Skip subtree if cutoff

        return best_score, best_action
