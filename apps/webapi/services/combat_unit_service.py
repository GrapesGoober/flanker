from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    FireControls,
    InitiativeState,
    MoveControls,
    Transform,
)
from webapi.models import SquadModel


class CombatUnitService:

    @staticmethod
    def delete_unit(
        gs: GameState,
        unit_id: UUID,
    ) -> None:
        unit_component = gs.try_component(unit_id, CombatUnit)
        if unit_component == None:
            raise ValueError(f"Combat unit {unit_id=} does not exist")
        # FIXME this simply deletes entity, but does not consider
        # other side effects, such as firing-at fields.
        # It should go through proper core systems for deleting units.
        gs.delete_entity(unit_id)

    @staticmethod
    def update_unit(
        gs: GameState,
        unit: SquadModel,
    ) -> None:
        unit_component = gs.get_component(unit.unit_id, CombatUnit)
        transform = gs.get_component(unit.unit_id, Transform)
        fire_controls = gs.get_component(unit.unit_id, FireControls)

        transform.position = unit.position
        transform.degrees = unit.degrees
        unit_component.status = unit.status
        unit_component.faction = (
            InitiativeState.Faction.BLUE
            if unit.is_friendly
            else InitiativeState.Faction.RED
        )
        fire_controls.fov_degrees = unit.fov_degrees
        fire_controls.firing_at = unit.firing_at

    @staticmethod
    def add_unit(
        gs: GameState,
        unit: SquadModel,
    ) -> None:
        gs.add_entity(
            CombatUnit(
                faction=(
                    InitiativeState.Faction.BLUE
                    if unit.is_friendly
                    else InitiativeState.Faction.RED
                ),
                status=unit.status,
            ),
            Transform(
                position=unit.position,
                degrees=unit.degrees,
            ),
            MoveControls(
                move_type=MoveControls.MoveType.FOOT,
            ),
            FireControls(
                fov_degrees=unit.fov_degrees,
                firing_at=unit.firing_at,
            ),
            AssaultControls(),
            id=unit.unit_id,
        )
