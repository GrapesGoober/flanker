from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LinearTransform, LosSystem
from matplotlib import pyplot as plt


def load_state(path: str) -> GameState:

    component_types: list[type[Any]] = []
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities, id_counter = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities, id_counter)
    return gs


def visualize_polygon(verts: list[Vec2], color: str = "C0", alpha: float = 0) -> None:
    xs = [v.x for v in verts]
    ys = [-v.y for v in verts]

    plt.scatter(xs, ys, color=color)  # type: ignore
    plt.fill(xs, ys, color=color, alpha=alpha)  # type: ignore
    plt.plot(xs, ys, linestyle="-", color=color)  # type: ignore
    plt.axis("equal")  # type: ignore


def draw_terrains(gs: GameState) -> None:

    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = LinearTransform.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        visualize_polygon(vertices, color="C1")


def draw_los(gs: GameState, unit_id: int) -> None:
    LosSystem.update_los_polygon(gs, unit_id)
    center = gs.get_component(unit_id, components.Transform).position
    poly = gs.get_component(unit_id, components.FireControls).los_polygon
    assert poly
    visualize_polygon(poly, color="C0", alpha=0.2)
    plt.scatter(center.x, -center.y, color="C0")  # type: ignore


if __name__ == "__main__":

    gs = load_state(path="./scenes/demo-simple.json")
    draw_los(gs, unit_id=10)
    plt.show()  # type: ignore
