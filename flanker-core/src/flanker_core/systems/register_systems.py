from flanker_core.gamestate import GameState
from flanker_core.systems.i_los_system import ILosSystem
from flanker_core.systems.los_system import LosSystem


def register_systems(gs: GameState) -> None:
    gs.register_system(ILosSystem, LosSystem)
