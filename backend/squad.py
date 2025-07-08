from core.components import Faction, CombatUnit, MoveControls, Transform
from core.vec2 import Vec2
from core.gamestate import GameState
from backend.models import SquadModel


class SquadController:

    @staticmethod
    def add_faction(gs: GameState, has_initiative: bool) -> int:
        return gs.add_entity(Faction(has_initiative))

    @staticmethod
    def add_squad(gs: GameState, pos: Vec2, command_id: int) -> int:
        return gs.add_entity(
            Transform(position=pos), MoveControls(), CombatUnit(command_id=command_id)
        )

    @staticmethod
    def get_squads(gs: GameState, friendly_command_id: int) -> list[SquadModel]:
        squads: list[SquadModel] = []
        for ent, unit, transform in gs.query(CombatUnit, Transform):
            squads.append(
                SquadModel(
                    unit_id=ent,
                    position=transform.position,
                    status=unit.status,
                    is_friendly=(unit.command_id == friendly_command_id),
                )
            )
        return squads
