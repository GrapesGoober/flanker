from math import inf
from typing import Tuple

from flanker_ai.i_game_state import IGameState


class MinimaxSearch:
    @staticmethod
    def search(
        state: IGameState,
        depth: int,
        maximizing: bool,
    ) -> Tuple[float, IGameState | None]:
        """
        Returns (best_score, best_child_state)
        """

        winner = state.get_winner()

        # Terminal or depth cutoff
        if depth == 0 or winner is not None:
            return state.get_score(), None

        branches = state.get_branches()

        if not branches:
            # No moves available
            return state.get_score(), None

        best_state = None

        if maximizing:
            best_score = -inf
            for child in branches:
                score, _ = MinimaxSearch.search(child, depth - 1, False)
                if score > best_score:
                    best_score = score
                    best_state = child
            return best_score, best_state

        else:
            best_score = inf
            for child in branches:
                score, _ = MinimaxSearch.search(child, depth - 1, True)
                if score < best_score:
                    best_score = score
                    best_state = child
            return best_score, best_state
