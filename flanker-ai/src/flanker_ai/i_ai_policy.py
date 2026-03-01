from typing import Protocol, Sequence, runtime_checkable

from flanker_ai.i_game_state import IRepresentationState


@runtime_checkable
class IAiPolicy[TAction](Protocol):
    """Interface for defining a decision policy for AI."""

    def get_action_sequence(self, rs: IRepresentationState[TAction]) -> Sequence[TAction]: ...
