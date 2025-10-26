from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from matplotlib import pyplot as plt
from backend.tag_components import TerrainTypeTag
from core import components
from core.gamestate import GameState
from core.systems.los_system import LosSystem
from core.utils.vec2 import Vec2


def visualize_points(verts: list[Vec2]) -> None:
    xs = [v.x for v in verts]
    ys = [-v.y for v in verts]

    plt.scatter(xs, ys)  # type: ignore
    plt.plot(xs, ys, linestyle="-")  # type: ignore
    plt.axis("equal")  # type: ignore
    plt.show()  # type: ignore


if __name__ == "__main__":

    component_types: list[type[Any]] = []
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)
    component_types.append(TerrainTypeTag)

    path = "./scenes/demo-simple.json"

    with open(path, "r") as f:
        gs = GameState.load(f.read(), component_types)

    poly = LosSystem.get_los_polygon(gs, Vec2(1, 1))
    visualize_points(poly)
