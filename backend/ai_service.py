from backend.combat_unit_service import CombatUnitService
from core.faction_system import FactionSystem
from core.gamestate import GameState
from core.components import Faction


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Perform a basic AI turn for the given faction."""
        faction_id = CombatUnitService.get_opponent_faction_id(gs)
        faction = gs.get_component(faction_id, Faction)
        if faction.has_initiative == False:
            return

        # For now, pass on initiative without any actions
        FactionSystem.flip_initiative(gs)
