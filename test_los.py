from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from matplotlib import pyplot as plt

from backend.tag_components import TerrainTypeTag
from core.gamestate import GameState
from core.models import components
from core.models.vec2 import Vec2
from core.serializer import Serializer
from core.systems.los_system import LinearTransform, LosSystem


def visualize_points(verts: list[Vec2], color: str = "C0") -> None:
    xs = [v.x for v in verts]
    ys = [-v.y for v in verts]

    plt.scatter(xs, ys, color=color)  # type: ignore
    plt.plot(xs, ys, linestyle="-", color=color)  # type: ignore
    plt.axis("equal")  # type: ignore


if __name__ == "__main__":

    component_types: list[type[Any]] = []
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)
    component_types.append(TerrainTypeTag)

    path = "./scenes/demo-simple.json"

    with open(path, "r") as f:
        entities, id_counter = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities, id_counter)

    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = LinearTransform.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        visualize_points(vertices, color="C1")
    unit_id = 10
    LosSystem.update_los_polygon(gs, unit_id)
    center = gs.get_component(unit_id, components.Transform).position
    poly = gs.get_component(unit_id, components.FireControls).los_polygon
    assert poly
    visualize_points(poly, color="C0")
    plt.scatter(center.x, -center.y, color="C0")  # type: ignore
    plt.show()  # type: ignore
