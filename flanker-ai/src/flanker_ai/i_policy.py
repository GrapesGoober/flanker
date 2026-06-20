from typing import Protocol, runtime_checkable

from flanker_ai.i_representation_state import IRepresentationState


@runtime_checkable
class IPolicy[TAction](Protocol):
    """Interface for defining a decision policy for AI."""

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, int]:
        """
        Returns a single best action from the search policy,
        if any, and its search size.
        """
        ...
