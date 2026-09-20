from typing import Protocol, runtime_checkable

from flanker_ai.i_representation_state import IRepresentationState


@runtime_checkable
class IPolicy[TAction, TLog](Protocol):
    """Interface for a domain independent AI game playing decision policy."""

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, TLog]:
        """
        Returns a single best action, if any, from the search policy and
        its search telemetry logs.
        """
        ...
