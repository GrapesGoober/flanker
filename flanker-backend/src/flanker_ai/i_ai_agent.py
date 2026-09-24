from dataclasses import dataclass
from typing import Protocol

from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState


@dataclass
class AiActionResult[TLog]:
    faction: InitiativeState.Faction
    action: Action
    result: ActionResult
    policy_log: TLog


class IAiAgent[TLog](Protocol):
    """Interface for a game-playing AI agent. The policy log is of type TLog."""

    def perform_action(
        self,
        gs: GameState,
    ) -> AiActionResult[TLog] | None:
        """
        Performs an action and return its result. This mutates the game state
        in place. Returns `None` if no legal actions possible.
        """
        ...
