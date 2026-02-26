from typing import Any

from flanker_ai.i_game_state import IGameState
from flanker_ai.models import Action
from flanker_core.gamestate import GameState


class IGameStateConverter[TAction, TState: IGameState[Any]]:
    """
    Provides logic to convert between original game state and
    AI representation game state
    """

    def create_template(self, gs: GameState) -> TState:
        """
        Create a template representation state from original state.
        Expensive precomputation goes here.
        """
        ...

    def update_template(
        self,
        gs: GameState,
        template: TState,
    ) -> TState:
        """Update the template representation state to make it ready for AI."""
        ...

    def deabstract_action(
        self,
        action: TAction,
        representation: TState,
        gs: GameState,
    ) -> Action:
        """
        Converts the abstract action within the abstract representation
        into a raw game state action."""
        ...
