from math import inf

from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class MinimaxSearch:
    "Minimax tree search with alpha-beta pruning."

    @staticmethod
    def search[T](
        state: IGameState[T],
        depth: int,
        alpha: float = -inf,
        beta: float = inf,
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
            # Have it prefer earlier win
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
        best_score = -inf if state.get_initiative() == MAXIMIZING_FACTION else inf

        for action in actions:
            # Assume the branches are deterministic
            branch = state.get_deterministic_branch(action)
            if branch is None:
                continue
            score, _ = MinimaxSearch.search(
                branch,
                depth - 1,
                alpha,
                beta,
            )

            if state.get_initiative() == MAXIMIZING_FACTION:
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
                break  # Beta cutoff

        return best_score, best_action
