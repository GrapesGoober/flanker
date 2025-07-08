from core.gamestate import GameState
from core.components import CombatUnit, Faction


class Command:
    """ECS System class for command hierarchy and faction initiative mechanic."""

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Flips the current initiative of command units."""
        for _, faction in gs.query(Faction):
            faction.has_initiative = not faction.has_initiative

    @staticmethod
    def has_initiative(gs: GameState, unit_id: int) -> bool:
        """Check the unit's command faction for initiative."""

        if (faction_id := Command.get_faction_id(gs, unit_id)) == None:
            return False
        if not (faction := gs.get_component(faction_id, Faction)):
            return False

        return faction.has_initiative

    @staticmethod
    def get_faction_id(gs: GameState, unit_id: int) -> int | None:
        """Get the unit's command faction entity id."""

        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return None
        # Recursively checks for the faction at the root of hierarchy tree
        if gs.get_component(unit.command_id, Faction):
            return unit.command_id
        else:
            return Command.get_faction_id(gs, unit.command_id)
