from core.faction_system import FactionSystem
from core.gamestate import GameState
from core.components import Faction


class BasicAiController:

    @staticmethod
    def play(gs: GameState, faction_id: int) -> None:
        if not (faction := gs.get_component(faction_id, Faction)):
            return
        if faction.has_initiative == False:
            return

        # Pass on initiative without any actions
        FactionSystem.flip_initiative(gs)
