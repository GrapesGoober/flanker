from math import inf
from typing import Callable

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.components import InitiativeState

_MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class ExpectimaxPolicy[TAction](IPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action(
        self,
        rs: IRepresentationState[TAction],
        callback: Callable[[], None] | None = None,
    ) -> TAction | None:
        """
        Returns the best actions sequence given a current game state.
        """
        _, action = self._search(rs, self._depth, callback)
        return action

    def _search(
        self,
        state: IRepresentationState[TAction],
        depth: int,
        callback: Callable[[], None] | None = None,
    ) -> tuple[float, TAction | None]:
        """
        Returns (best_score, best_action)
        """

        # Check for early cutoff
        winner = state.get_winner()
        if winner is not None:  # Winner found
            # Have it prefer earlier win by offsetting score with depth
            if winner == _MAXIMIZING_FACTION:
                return state.get_score(_MAXIMIZING_FACTION) + depth, None
            else:
                return state.get_score(_MAXIMIZING_FACTION) - depth, None

        if depth == 0:
            return state.get_score(_MAXIMIZING_FACTION), None

        actions = state.get_actions()
        if not actions:  # No moves available
            return state.get_score(_MAXIMIZING_FACTION), None

        best_action: TAction | None = None
        best_score = -inf if state.get_initiative() == _MAXIMIZING_FACTION else inf

        for action in actions:
            branches = state.get_branches(action)
            if branches == []:
                continue  # Escapes; prevents expected_score=0 being used
            expected_score = 0
            for probability, branch in branches:
                score, _ = self._search(
                    branch,
                    depth - 1,
                    callback,
                )
                expected_score += score * probability
            if state.get_initiative() == _MAXIMIZING_FACTION:
                if expected_score > best_score:
                    best_score = expected_score
                    best_action = action
            else:
                if expected_score < best_score:
                    best_score = expected_score
                    best_action = action

        return best_score, best_action
