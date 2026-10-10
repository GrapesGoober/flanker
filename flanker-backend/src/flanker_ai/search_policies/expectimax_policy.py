from dataclasses import dataclass
from itertools import count
from math import inf

from flanker_ai.search_states.i_search_state import ISearchState
from flanker_core.models.components import InitiativeState

_MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass
class _TranspositionEntry:
    score: float
    depth_remaining: int


@dataclass
class ExpectimaxSearchLog:
    tree_size: int


class ExpectimaxPolicy[TAction]:
    """
    Implements Expectimax game-tree search.
    """

    @staticmethod
    def get_action(
        rs: ISearchState[TAction],
        depth: int,
    ) -> tuple[TAction | None, ExpectimaxSearchLog]:
        """
        Returns the best action and its search log given a current game state.
        """

        counter = count(0)
        _, action = ExpectimaxPolicy[TAction]._search(
            state=rs,
            depth_remaining=depth,
            counter=counter,
            transposition_table={},
        )
        return action, ExpectimaxSearchLog(
            tree_size=next(counter) - 1,
        )

    @staticmethod
    def _search(
        state: ISearchState[TAction],
        depth_remaining: int,
        counter: "count[int]",
        transposition_table: dict[object, _TranspositionEntry],
    ) -> tuple[float, TAction | None]:

        next(counter)

        # Have early return for terminal states and leaf nodes.
        if state.get_winner() is not None or depth_remaining == 0:
            return state.get_score(_MAXIMIZING_FACTION), None
        actions = state.get_actions()
        if len(actions) == 0:  # No legal actions => lost
            return state.get_score(_MAXIMIZING_FACTION), None

        # Loop through each action and recursively expand tree
        is_maximizing = state.get_initiative() == _MAXIMIZING_FACTION
        best_action: TAction | None = None
        best_score = -inf if is_maximizing else inf
        for action in actions:
            branches = state.get_branches(action)
            if branches == []:
                continue
            expected_score = 0
            for probability, branch in branches:

                new_branch_depth = depth_remaining - 1
                state_key = branch.get_hashable_key()
                cached_entry = transposition_table.get(state_key)

                # Reuse the cached score value if exist, but also only if the
                # cached entry is more near-root than the current ply.
                if (
                    cached_entry is not None
                    and cached_entry.depth_remaining >= new_branch_depth
                ):
                    score = cached_entry.score
                else:
                    score, _ = ExpectimaxPolicy[TAction]._search(
                        state=branch,
                        depth_remaining=new_branch_depth,
                        counter=counter,
                        transposition_table=transposition_table,
                    )
                    transposition_table[state_key] = _TranspositionEntry(
                        score=score,
                        depth_remaining=new_branch_depth,
                    )

                expected_score += score * probability

            # Have scores be closer to zero the further down the tree.
            # This numbs the impact of future gains or future losses.
            # Ex: future wins is less preferable than closer wins.
            expected_score = expected_score * 0.9

            # Update score
            if is_maximizing:
                if expected_score > best_score:
                    best_score = expected_score
                    best_action = action
            else:
                if expected_score < best_score:
                    best_score = expected_score
                    best_action = action

        return best_score, best_action
