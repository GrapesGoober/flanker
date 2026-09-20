from dataclasses import dataclass

from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult


@dataclass
class AiActionResult:
    action: Action
    result: ActionResult
    result_gs: GameState
    search_log: AiSearchLog


class IAiAgent:
    """Interface for a game-playing AI agent."""

    def perform_action(self, gs: GameState) -> AiActionResult | None:
        """
        Performs an action and return its result. This mutates the game state
        in place. Returns `None` if no legal actions possible.
        """
        ...
