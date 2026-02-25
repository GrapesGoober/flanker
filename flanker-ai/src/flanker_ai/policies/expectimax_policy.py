from typing import Sequence

from flanker_ai.i_ai_policy import IAiPolicy
from flanker_ai.i_game_state import IGameState
from flanker_ai.policies.expectimax_search import ExpectimaxSearch
from flanker_core.models.components import InitiativeState

count = 0
MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


class ExpectimaxPolicy[TAction](IAiPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action_sequence(self, gs: IGameState[TAction]) -> Sequence[TAction]:
        """
        Returns the best actions sequence given a current game state.
        """
        _, action = ExpectimaxSearch.search(gs, self._depth)
        if action == None:
            return []
        return [action]
