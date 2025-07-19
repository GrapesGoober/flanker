from core.gamestate import GameState
from core.components import CombatUnit, Faction, FireControls


class FactionSystem:
    """ECS System class for faction and initiative mechanic."""

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Flips the current initiative of command units."""
        for _, faction in gs.query(Faction):
            faction.has_initiative = not faction.has_initiative
        # Reset reactive fire
        for _, fire_controls in gs.query(FireControls):
            fire_controls.can_reactive_fire = True

    @staticmethod
    def set_initiative(gs: GameState, faction_id: int) -> None:
        """Sets the given faction to have the initiative."""

        for id, faction in gs.query(Faction):
            faction.has_initiative = False
            if id == faction_id:
                faction.has_initiative = True

        # Reset reactive fire
        for id, fire_controls in gs.query(FireControls):
            if FactionSystem.get_faction_id(gs, id) == faction_id:
                fire_controls.can_reactive_fire = True

    @staticmethod
    def has_initiative(gs: GameState, unit_id: int) -> bool:
        """Check the unit's command faction for initiative."""
        faction_id = FactionSystem.get_faction_id(gs, unit_id)
        faction = gs.get_component(faction_id, Faction)
        return faction.has_initiative

    @staticmethod
    def get_faction_id(gs: GameState, unit_id: int, depth: int = 10) -> int:
        """Get the unit's command faction entity id. Limited tree depth."""
        if depth <= 0:
            raise Exception(f"Can't find root {Faction} for {unit_id=}")

        # Recursively checks for the faction at the root of hierarchy tree
        unit = gs.get_component(unit_id, CombatUnit)
        if gs.try_component(unit.command_id, Faction):
            return unit.command_id
        else:
            depth -= 1
            return FactionSystem.get_faction_id(gs, unit.command_id)
