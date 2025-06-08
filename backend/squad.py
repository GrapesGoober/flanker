from core.components import CommandUnit, CombatUnit, MoveControls, Transform
from core.vec2 import Vec2
from core.gamestate import GameState
from backend.models import SquadModel


class SquadController:

    @staticmethod
    def add_command(gs: GameState, pos: Vec2) -> int:
        return gs.add_entity(CommandUnit())

    @staticmethod
    def add_squad(gs: GameState, pos: Vec2, command_id: int) -> int:
        return gs.add_entity(
            Transform(position=pos), MoveControls(), CombatUnit(command_id=command_id)
        )

    @staticmethod
    def get_squads(gs: GameState) -> list[SquadModel]:
        squads: list[SquadModel] = []
        for ent, unit, transform in gs.query(CombatUnit, Transform):
            squads.append(
                SquadModel(unit_id=ent, position=transform.position, status=unit.status)
            )
        return squads
