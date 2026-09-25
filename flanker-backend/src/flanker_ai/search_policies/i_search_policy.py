from typing import Protocol, runtime_checkable

from flanker_ai.search_states.i_search_state import ISearchState


@runtime_checkable
class ISearchPolicy[TAction, TLog](Protocol):
    """
    Interface for a domain independent search decision policy.
    The action space is of type TAction, and log type is TLog.
    """

    def get_action(
        self,
        rs: ISearchState[TAction],
    ) -> tuple[TAction | None, TLog]:
        """
        Returns a single best action, if any, from the search policy and
        its search telemetry logs.
        """
        ...
