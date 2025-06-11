from core.gamestate import GameState
from core.components import CombatUnit, CommandUnit


class Command:
    """Static class for command hierarchy and initiative mechanic."""

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Flips the current initiative of command units."""
        for _, command in gs.query(CommandUnit):
            command.has_initiative = not command.has_initiative

    @staticmethod
    def has_initiative(gs: GameState, unit_id: int) -> bool:
        """Check the root of a unit's command hierarchy for initiative."""
        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return False
        if not (command := gs.get_component(unit.command_id, CommandUnit)):
            return False
        return command.has_initiative
