from core.command import Command
from core.components import (
    Faction,
    CombatUnit,
    FireControls,
    MoveControls,
    Transform,
)
from core.vec2 import Vec2
from core.gamestate import GameState
from backend.models import CombatUnitsViewState, SquadModel


class CombatUnitController:

    @staticmethod
    def add_faction(gs: GameState, has_initiative: bool) -> int:
        return gs.add_entity(Faction(has_initiative))

    @staticmethod
    def add_squad(gs: GameState, pos: Vec2, command_id: int) -> int:
        return gs.add_entity(
            Transform(position=pos),
            MoveControls(),
            CombatUnit(command_id=command_id),
            FireControls(),
        )

    @staticmethod
    def get_units(gs: GameState, faction_id: int) -> CombatUnitsViewState:

        if not (faction := gs.get_component(faction_id, Faction)):
            raise Exception(f"Entity {faction_id} does not have component {Faction}")

        squads: list[SquadModel] = []
        for ent, unit, transform in gs.query(CombatUnit, Transform):
            if (unit_faction_id := Command.get_faction_id(gs, ent)) == None:
                raise Exception(f"Unit id {ent} doesn't have parent faction")
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
