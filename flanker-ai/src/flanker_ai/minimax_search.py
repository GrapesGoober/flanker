from math import inf
from typing import Tuple

from flanker_ai.i_game_state import IGameState


class MinimaxSearch:
    @staticmethod
    def search[T](
        state: IGameState[T],
        depth: int,
        maximizing: bool,
    ) -> Tuple[float, T | None]:
        """
        Returns (best_score, best_action)
        """

        winner = state.get_winner()

        # Terminal or depth cutoff
        if depth == 0 or winner is not None:
            return state.get_score(), None

        actions = state.get_actions()
        if not actions:  # No moves available
            return state.get_score(), None

        best_action: T | None = None
        if maximizing:
            best_score = -inf
            for action in actions:
                branches = state.get_branches(action)
                if not branches:  # No branching available
                    return state.get_score(), None
                # This assumes deterministic outcome (normal minimax)
                for branch in branches:
                    score, _ = MinimaxSearch.search(branch, depth - 1, False)
                    if score > best_score:
                        best_score = score
                        best_action = action
            return best_score, best_action

        else:
            best_score = inf
            for action in actions:
                branches = state.get_branches(action)
                if not branches:  # No branching available
                    return state.get_score(), None
                # This assumes deterministic outcome (normal minimax)
                for branch in branches:
                    score, _ = MinimaxSearch.search(branch, depth - 1, True)
                    if score < best_score:
                        best_score = score
                        best_action = action
            return best_score, best_action
