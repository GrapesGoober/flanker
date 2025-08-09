from core.components import Faction
from core.faction_system import FactionSystem
from core.gamestate import GameState


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Perform a basic AI turn for the given faction."""
        # Assume that the AI plays RED
        if FactionSystem.get_initiative(gs) != Faction.FactionType.RED:
            return

        # For now, pass on initiative without any actions
        FactionSystem.flip_initiative(gs)
