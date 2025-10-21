from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID
from backend.terrain_service import TerrainTypeTag
from core import components
from core.action_models import MoveAction
from core.gamestate import GameState
from core.serializer import Serializer
from core.systems.move_system import MoveSystem
from core.utils.vec2 import Vec2

component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)
component_types.append(TerrainTypeTag)

path = "./scenes/demo-old.json"

with open(path, "r") as f:
    gs = GameState(Serializer.deserialize(f.read(), component_types))


MoveSystem.move(
    gs,
    MoveAction(
        UUID("62fd16ad-d6aa-4afb-aaa0-eea036b30d1a"),
        Vec2(-50, -200),
    ),
)


def test() -> None:
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("e7b7790d-8f6e-444e-9221-29e5236d5944"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("224c2dcf-3ed5-4f59-9304-62a5982c8ac5"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("59dbc668-5392-484c-a99f-93e856d44ca5"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("2544a305-4c9e-478c-a024-95bc4e2be343"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("df04b011-6735-498d-8b64-48874f4a4f16"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("c3e0d53d-ce00-4315-950e-14c15b62abe1"),
            Vec2(-50, -200),
        ),
    )
    MoveSystem.move(
        gs,
        MoveAction(
            UUID("4ec54809-81c2-4319-9c18-927002bb970b"),
            Vec2(-50, -200),
        ),
    )

    MoveSystem.move(
        gs,
        MoveAction(
            UUID("d6465f31-ea1a-435c-885b-fb31f1d96cce"),
            Vec2(-50, -200),
        ),
    )


from timeit import timeit

exec_time = timeit(test, number=1)
print(f"Execution time: {exec_time:.6f} seconds")

# import cProfile
# import pstats

# cProfile.run("test()", sort="tottime", filename="perftest.txt")
# p = pstats.Stats("perftest.txt")
# p.sort_stats("tottime")
# p.print_stats(20)
