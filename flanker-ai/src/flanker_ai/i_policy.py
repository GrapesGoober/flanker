from typing import Callable, Protocol, runtime_checkable

from flanker_ai.i_representation_state import IRepresentationState


@runtime_checkable
class IPolicy[TAction](Protocol):
    """Interface for defining a decision policy for AI."""

    def get_action(
        self,
        rs: IRepresentationState[TAction],
        callback: Callable[[], None] | None = None,
    ) -> TAction | None: ...
