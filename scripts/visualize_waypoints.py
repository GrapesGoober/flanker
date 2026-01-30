from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LinearTransform
from matplotlib import pyplot as plt


def visualize_polygon(verts: list[Vec2], color: str = "C0") -> None:
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
        visualize_polygon(vertices, color="C1")

    waypoint_gs = WaypointScheme.create_grid_waypoints(gs, spacing=20)
    for point in waypoint_gs.waypoints.values():
        plt.scatter(point.position.x, -point.position.y, color="C0")  # type: ignore

    plt.show()  # type: ignore
