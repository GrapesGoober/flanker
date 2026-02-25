from typing import Any
from flanker_ai.i_game_state import IGameState
from flanker_ai.unabstracted.models import ActionResult
from flanker_core.gamestate import GameState
from flanker_core.models.outcomes import InvalidAction


class IGameStateConverter[TAction]:
    """
    Provides logic to convert between original game state and
    AI representation game state
    """

    def create_template(self, gs: GameState) -> IGameState[TAction]:
        """
        Create a template representation state from original state.
        Expensive precomputation goes here.
        """
        ...

    def update_template(
        self,
        gs: GameState,
        template: IGameState[TAction],
    ) -> IGameState[TAction]:
        """Update the template representation state to make it ready for AI."""
        ...

    def apply_action[T: IGameState[Any]](
        self,
        action: TAction,
        representation: IGameState[TAction],
        gs: GameState,
    ) -> ActionResult | InvalidAction: ...
