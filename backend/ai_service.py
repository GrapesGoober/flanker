from core.components import FactionManager
from core.faction_system import FactionSystem
from core.gamestate import GameState


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Perform a basic AI turn for the given faction."""
        # Assume that the AI plays FACTION_B
        if FactionSystem.get_initiative(gs) != FactionManager.FactionType.FACTION_B:
            return

        # For now, pass on initiative without any actions
        FactionSystem.flip_initiative(gs)
