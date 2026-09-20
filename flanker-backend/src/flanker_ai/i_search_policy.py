from typing import Protocol, runtime_checkable

from flanker_ai.i_search_state import ISearchState


@runtime_checkable
class ISearchPolicy[TAction, TLog](Protocol):
    """Interface for a domain independent search decision policy."""

    def get_action(
        self,
        rs: ISearchState[TAction],
    ) -> tuple[TAction | None, TLog]:
        """
        Returns a single best action, if any, from the search policy and
        its search telemetry logs.
        """
        ...
