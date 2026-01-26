from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    MoveControls,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem

from webapi.models import CombatUnitsViewState, SquadModel


class CombatUnitService:
    """Provides static methods to add and query combat units and factions."""

    @staticmethod
    def add_squad(
        gs: GameState,
        pos: Vec2,
        command_id: int,
        faction: InitiativeState.Faction,
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
    def get_units_view_state(gs: GameState) -> CombatUnitsViewState:
        """Get all squads for a given faction as a view state."""
        # Assume player faction is BLUE
        faction = InitiativeState.Faction.BLUE
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

        has_initiative = InitiativeSystem.get_initiative(gs) == faction
        winning_faction = ObjectiveSystem.get_winning_faction(gs)

        if winning_faction == faction:
            objective_state = CombatUnitsViewState.ObjectiveState.COMPLETED
        elif winning_faction == None:
            objective_state = CombatUnitsViewState.ObjectiveState.INCOMPLETE
        else:
            objective_state = CombatUnitsViewState.ObjectiveState.FAILED

        return CombatUnitsViewState(
            objective_state=objective_state,
            has_initiative=has_initiative,
            squads=squads,
        )
