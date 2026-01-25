from timeit import timeit
from ai.minimax_player import MinimaxPlayer
from core.gamestate import GameState
from core.models.components import (
    InitiativeState,
)
from core.systems.initiative_system import InitiativeSystem
from webapi.logging_service import LoggingService


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Not implemented. This AI will just pass initiative."""
        # Assume that the AI plays RED
        faction = InitiativeState.Faction.RED
        if InitiativeSystem.get_initiative(gs) != faction:
            return

        # For now, pass on initiative without any actions
        InitiativeSystem.flip_initiative(gs)


    @staticmethod
    def play_minimax(gs: GameState) -> None:
        
        def test() -> None:
            _, logs = MinimaxPlayer.play_minimax(gs, 4)
            for log in logs:
                LoggingService.log(gs, log)

        exec_time = timeit(test, number=1)
        print(f"Execution time: {exec_time:.6f} seconds")
