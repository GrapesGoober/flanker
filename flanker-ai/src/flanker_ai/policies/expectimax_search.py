from math import inf

from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class ExpectimaxSearch:

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
            branches = state.get_branches(action)
            if branches == []:
                continue  # Escapes; prevents expected_score=0 being used
            expected_score = 0
            for probability, branch in branches:
                score, _ = ExpectimaxSearch.search(
                    branch,
                    depth - 1,
                )
                expected_score += score * probability
            if state.get_initiative() == MAXIMIZING_FACTION:
                if expected_score > best_score:
                    best_score = expected_score
                    best_action = action
            else:
                if expected_score < best_score:
                    best_score = expected_score
                    best_action = action

        return best_score, best_action
