from flanker_core.gamestate import GameState
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem


def register_systems(gs: GameState) -> None:
    gs.register(AssaultSystem)
    gs.register(CommandSystem)
    gs.register(FireSystem)
    gs.register(InitiativeSystem)
    gs.register(IntersectSystem)
    gs.register(LosSystem)
    gs.register(MoveSystem)
    gs.register(ObjectiveSystem)
