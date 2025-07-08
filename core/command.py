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
        """Check the root of a unit's command hierarchy for initiative."""
        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return False
        if not (command := gs.get_component(unit.command_id, Faction)):
            return False
        return command.has_initiative
