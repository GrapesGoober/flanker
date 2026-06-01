from flanker_ai.config_models import UnabstractedStateConfig
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_core.gamestate import GameState


class UnabstractedStateFactory:
    @staticmethod
    def create_state(
        gs: GameState,
        config: UnabstractedStateConfig,
    ) -> UnabstractedState:
        return UnabstractedState(gs, move_candidates="Random")
