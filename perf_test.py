from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from backend.terrain_service import TerrainTypeTag
from core import components
from core.gamestate import GameState
from core.move_system import MoveSystem
from core.utils.vec2 import Vec2
import cProfile


component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)
component_types.append(TerrainTypeTag)

path = "./scenes/demo.json"

with open(path, "r") as f:
    gs = GameState.load(f.read(), component_types)


def normal_move() -> None:
    MoveSystem.move(gs, 1, Vec2(-50, -200))
    MoveSystem.move(gs, 2, Vec2(-50, -200))
    MoveSystem.move(gs, 3, Vec2(-50, -200))
    MoveSystem.move(gs, 4, Vec2(-50, -200))
    MoveSystem.move(gs, 5, Vec2(-50, -200))
    MoveSystem.move(gs, 6, Vec2(-50, -200))


# exec_time = timeit(normal_move, number=1)
# print(f"Execution time: {exec_time:.6f} seconds")
cProfile.run("normal_move()", sort="tottime")
