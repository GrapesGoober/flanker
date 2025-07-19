from core.faction_system import FactionSystem
from core.gamestate import GameState
from core.components import Faction


class BasicAiController:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState, faction_id: int) -> None:
        """Perform a basic AI turn for the given faction."""
        faction = gs.get_component(faction_id, Faction)
        if faction.has_initiative == False:
            return

        # For now, pass on initiative without any actions
        FactionSystem.flip_initiative(gs)
