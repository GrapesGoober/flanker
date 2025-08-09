from core.gamestate import GameState
from core.components import CombatUnit, InitiativeState, FireControls


class InitiativeSystem:
    """ECS System class for initiative mechanic."""

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Flips the current initiative of command units."""
        for _, initiative in gs.query(InitiativeState):
            match initiative.faction:
                case InitiativeState.Faction.RED:
                    initiative.faction = InitiativeState.Faction.BLUE
                case InitiativeState.Faction.BLUE:
                    initiative.faction = InitiativeState.Faction.RED
        # Reset reactive fire
        for _, fire_controls in gs.query(FireControls):
            fire_controls.can_reactive_fire = True

    @staticmethod
    def set_initiative(gs: GameState, faction: InitiativeState.Faction) -> None:
        """Sets the given faction to have the initiative."""
        for _, faction_manager in gs.query(InitiativeState):
            faction_manager.faction = faction
        # Reset reactive fire
        for _, unit, fire_controls in gs.query(CombatUnit, FireControls):
            if unit.faction == faction:
                fire_controls.can_reactive_fire = True

    @staticmethod
    def has_initiative(gs: GameState, unit_id: int) -> bool:
        """Check whether the unit's faction has initiative."""
        unit = gs.get_component(unit_id, CombatUnit)
        return unit.faction == InitiativeSystem.get_initiative(gs)

    @staticmethod
    def get_initiative(gs: GameState) -> InitiativeState.Faction:
        for _, faction in gs.query(InitiativeState):
            return faction.faction
        raise Exception("FactionManager component not found")
