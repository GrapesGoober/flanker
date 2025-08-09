from core.faction_system import FactionSystem
from core.components import (
    CombatUnit,
    Faction,
    FireControls,
    MoveControls,
    Transform,
)
from core.utils.vec2 import Vec2
from core.gamestate import GameState
from backend.models import CombatUnitsViewState, SquadModel


class CombatUnitService:
    """Provides static methods to add and query combat units and factions."""

    @staticmethod
    def add_squad(
        gs: GameState,
        pos: Vec2,
        command_id: int,
        faction: Faction.FactionType,
    ) -> int:
        """Add a new squad to the game state for a given faction."""
        return gs.add_entity(
            Transform(position=pos),
            MoveControls(),
            CombatUnit(
                command_id=command_id,
                faction=faction,
            ),
            FireControls(),
        )

    @staticmethod
    def get_units(gs: GameState) -> CombatUnitsViewState:
        """Get all squads for a given faction as a view state."""
        # Assume player faction is BLUE
        faction = Faction.FactionType.BLUE
        squads: list[SquadModel] = []
        for ent, unit, transform, fire in gs.query(
            CombatUnit,
            Transform,
            FireControls,
        ):
            squads.append(
                SquadModel(
                    unit_id=ent,
                    position=transform.position,
                    status=unit.status,
                    is_friendly=(unit.faction == faction),
                    no_fire=not fire.can_reactive_fire,
                )
            )

        has_initiative = FactionSystem.get_initiative(gs) == faction
        return CombatUnitsViewState(
            has_initiative=has_initiative,
            squads=squads,
        )
