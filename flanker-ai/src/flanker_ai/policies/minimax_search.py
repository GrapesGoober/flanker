from math import inf
from typing import Tuple

from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

count = 0


class MinimaxSearch:
    @staticmethod
    def search[T](
        state: IGameState[T],
        depth: int,
    ) -> Tuple[float, T | None]:
        """
        Returns (best_score, best_action)
        """

        global count
        print(count)
        count += 1

        # Check for early cutoff
        winner = state.get_winner()
        if winner is not None:  # Winner found
            # TODO: write a state-independent maximizing
            # way to prefer shallower wins
            match winner:
                case InitiativeState.Faction.BLUE:
                    return state.get_score() + depth, None
                case InitiativeState.Faction.RED:
                    return state.get_score() - depth, None
        if depth == 0 or winner is not None:
            return state.get_score(), None
        actions = state.get_actions()
        if not actions:  # No moves available
            return state.get_score(), None

        best_action: T | None = None
        if state.is_maximizing():
            best_score = -inf
            for action in actions:
                branches = state.get_branches(action)
                if not branches:  # No branching available
                    return state.get_score(), None
                # This assumes deterministic outcome (normal minimax)
                for branch in branches:
                    score, _ = MinimaxSearch.search(branch, depth - 1)
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
                    score, _ = MinimaxSearch.search(branch, depth - 1)
                    if score < best_score:
                        best_score = score
                        best_action = action
            return best_score, best_action
