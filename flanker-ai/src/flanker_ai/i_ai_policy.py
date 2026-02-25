from typing import Protocol, Sequence, runtime_checkable

from flanker_ai.i_game_state import IGameState


@runtime_checkable
class IAiPolicy[TAction](Protocol):
    """Interface for defining a decision policy for AI."""

    def get_action_sequence(self, gs: IGameState[TAction]) -> Sequence[TAction]: ...
