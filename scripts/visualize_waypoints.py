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
from matplotlib.collections import LineCollection


def visualize_polyline(verts: list[Vec2], color: str = "C0") -> None:
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

    # Plot terrain in orange
    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = LinearTransform.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        visualize_polyline(vertices, color="C1")

    # Plot the waypoints in blue
    print("Creating waypoints...")
    waypoint_gs = WaypointScheme.create_grid_waypoints(gs, spacing=20, offset=10)
    print("Creating waypoints done, drawing waypoints")
    segments: list[list[tuple[float, float]]] = []
    points_x: list[float] = []
    points_y: list[float] = []
    ids: list[int] = []
    for id, point in waypoint_gs.waypoints.items():
        points_x.append(point.position.x)
        points_y.append(-point.position.y)
        ids.append(id)

        # Draw the interconnected visibility
        for visible_node_id in point.visible_nodes:
            visible_node = waypoint_gs.waypoints[visible_node_id]
            segments.append(
                [
                    (point.position.x, -point.position.y),
                    (visible_node.position.x, -visible_node.position.y),
                ]
            )

    # Draw all points at once
    plt.scatter(points_x, points_y, color="C0", s=5)  # type: ignore
    for x, y, id_ in zip(points_x, points_y, ids):
        plt.text(x, y, str(id_), fontsize=6, ha="left", va="bottom")  # type: ignore

    # Draw all lines at once
    lc = LineCollection(segments, colors="C0", linewidths=0.5, alpha=0.1)
    plt.gca().add_collection(lc)

    plt.show()  # type: ignore
