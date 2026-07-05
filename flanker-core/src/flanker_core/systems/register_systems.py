from flanker_core.gamestate import GameState
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.systems.los_system import LosSystem


def register_systems(gs: GameState) -> None:
    gs.register(IntersectSystem)
    gs.register(LosSystem)
