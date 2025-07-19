from core.faction_system import FactionSystem
from core.components import (
    Faction,
    CombatUnit,
    FireControls,
    MoveControls,
    Transform,
)
from core.utils.vec2 import Vec2
from core.gamestate import GameState
from backend.models import CombatUnitsViewState, SquadModel


class CombatUnitController:
    """Provides static methods to add and query combat units and factions."""

    @staticmethod
    def add_faction(gs: GameState, has_initiative: bool) -> int:
        """Add a new faction to the game state."""
        return gs.add_entity(Faction(has_initiative))

    @staticmethod
    def add_squad(gs: GameState, pos: Vec2, command_id: int) -> int:
        """Add a new squad to the game state for a given faction."""
        return gs.add_entity(
            Transform(position=pos),
            MoveControls(),
            CombatUnit(command_id=command_id),
            FireControls(),
        )

    @staticmethod
    def get_units(gs: GameState, faction_id: int) -> CombatUnitsViewState:
        """Get all squads for a given faction as a view state."""
        faction = gs.get_component(faction_id, Faction)
        squads: list[SquadModel] = []
        for ent, unit, transform in gs.query(CombatUnit, Transform):
            unit_faction_id = FactionSystem.get_faction_id(gs, ent)
            squads.append(
                SquadModel(
                    unit_id=ent,
                    position=transform.position,
                    status=unit.status,
                    is_friendly=(unit_faction_id == faction_id),
                )
            )

        return CombatUnitsViewState(
            has_initiative=faction.has_initiative, squads=squads
        )
