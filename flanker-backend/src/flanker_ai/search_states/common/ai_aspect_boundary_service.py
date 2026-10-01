from flanker_core.gamestate import GameState
from flanker_core.models.components import Transform


class AiAspectBoundaryService:

    @staticmethod
    def get_aspects(
        gs: GameState,
        transform: Transform,
    ) -> list[float]:
        return [45 * i for i in range(0, 8)]
