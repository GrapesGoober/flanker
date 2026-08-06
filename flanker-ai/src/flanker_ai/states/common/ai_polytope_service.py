from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2


class AiPolytopeService:
    @staticmethod
    def get_polytope(gs: GameState) -> list[Vec2]: ...
