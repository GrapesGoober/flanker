from typing import Protocol, runtime_checkable

from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action


@runtime_checkable
class IHeuristicPolicy[TLog](Protocol):
    """Interface for a domain dependent (Flanker) AI game playing decision policy."""

    def get_action(
        self,
        gs: GameState,
    ) -> tuple[Action, TLog]:
        """
        Returns a single best action, if any, from the policy and
        its search telemetry logs.
        """
        ...
