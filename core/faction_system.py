from core.gamestate import GameState
from core.components import CombatUnit, Faction, FireControls


class FactionSystem:
    """ECS System class for faction and initiative mechanic."""

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Flips the current initiative of command units."""
        for _, faction in gs.query(Faction):
            match faction.active_faction:
                case Faction.FactionType.RED:
                    faction.active_faction = Faction.FactionType.BLUE
                case Faction.FactionType.BLUE:
                    faction.active_faction = Faction.FactionType.RED
        # Reset reactive fire
        for _, fire_controls in gs.query(FireControls):
            fire_controls.can_reactive_fire = True

    @staticmethod
    def set_initiative(gs: GameState, faction: Faction.FactionType) -> None:
        """Sets the given faction to have the initiative."""
        for _, faction_manager in gs.query(Faction):
            faction_manager.active_faction = faction
        # Reset reactive fire
        for _, unit, fire_controls in gs.query(CombatUnit, FireControls):
            if unit.faction == faction:
                fire_controls.can_reactive_fire = True

    @staticmethod
    def has_initiative(gs: GameState, unit_id: int) -> bool:
        """Check whether the unit's faction has initiative."""
        unit = gs.get_component(unit_id, CombatUnit)
        return unit.faction == FactionSystem.get_initiative(gs)

    @staticmethod
    def get_initiative(gs: GameState) -> Faction.FactionType:
        for _, faction in gs.query(Faction):
            return faction.active_faction
        raise Exception("FactionManager component not found")
