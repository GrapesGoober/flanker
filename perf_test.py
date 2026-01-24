from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from webapi.terrain_service import TerrainTypeTag
from core.gamestate import GameState
from core.models import components
from core.models.vec2 import Vec2
from core.serializer import Serializer
from core.systems.move_system import MoveSystem

component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)
component_types.append(TerrainTypeTag)

path = "./scenes/demo.json"

with open(path, "r") as f:
    entities, id_counter = Serializer.deserialize(
        json_data=f.read(),
        component_types=component_types,
    )
    gs = GameState.load(entities, id_counter)


MoveSystem.move(gs, 1, Vec2(-50, -200))


def test() -> None:

    # Reset LOS polygons
    for _, fire_controls in gs.query(components.FireControls):
        fire_controls.los_polygon = None
    MoveSystem.move(gs, 2, Vec2(-50, -200))
    MoveSystem.move(gs, 3, Vec2(-50, -200))
    MoveSystem.move(gs, 4, Vec2(-50, -200))
    MoveSystem.move(gs, 5, Vec2(-50, -200))
    MoveSystem.move(gs, 6, Vec2(-50, -200))
    MoveSystem.move(gs, 7, Vec2(-50, -200))
    MoveSystem.move(gs, 8, Vec2(-50, -200))
    MoveSystem.move(gs, 9, Vec2(-50, -200))


from timeit import timeit

exec_time = timeit(test, number=1)
print(f"Execution time: {exec_time:.6f} seconds")

# import cProfile
# import pstats

# cProfile.run("test()", sort="tottime", filename="perftest.txt")
# p = pstats.Stats("perftest.txt")
# p.sort_stats("tottime")
# p.print_stats(20)
