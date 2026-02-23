from math import inf

from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class MinimaxSearch:
    @staticmethod
    def search[T](
        state: IGameState[T],
        depth: int,
    ) -> tuple[float, T | None]:
        """
        Returns (best_score, best_action)
        """

        global count
        if count % 50000 == 0:
            print(count)
        count += 1

        # Check for early cutoff
        winner = state.get_winner()
        if winner is not None:  # Winner found
            if winner == MAXIMIZING_FACTION:
                return state.get_score(MAXIMIZING_FACTION) + depth, None
            else:
                return state.get_score(MAXIMIZING_FACTION) - depth, None
        if depth == 0:
            return state.get_score(MAXIMIZING_FACTION), None
        actions = state.get_actions()
        if not actions:  # No moves available
            return state.get_score(MAXIMIZING_FACTION), None

        best_action: T | None = None
        if state.get_initiative() == MAXIMIZING_FACTION:
            best_score = -inf
            for action in actions:
                branches = state.get_branches(action)
                if not branches:  # No branching available
                    return state.get_score(MAXIMIZING_FACTION), None
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
                    return state.get_score(MAXIMIZING_FACTION), None
                # This assumes deterministic outcome (normal minimax)
                for branch in branches:
                    score, _ = MinimaxSearch.search(branch, depth - 1)
                    if score < best_score:
                        best_score = score
                        best_action = action
            return best_score, best_action
