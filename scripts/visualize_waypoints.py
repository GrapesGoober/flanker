from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LinearTransform, LosSystem
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection


def load_state(path: str) -> GameState:

    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
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


def draw_waypoints(gs: GameState, faction: InitiativeState.Faction) -> None:

    print("Creating waypoints...")

    config = AiAgent.get_state_config(gs, faction)

    assert isinstance(
        config, AiConfigComponent.WaypointsStateConfig
    ), "Can't visualize non-waypoints AI config"

    waypoints_gs = WaypointsState(
        points=config.waypoint_coordinates,
        path_tolerance=10,
    )

    waypoints_gs.initialize_state(gs)
    waypoints_gs.update_state(gs)

    print("Drawing waypoints...")

    segments: list[list[tuple[float, float]]] = []
    points_x: list[float] = []
    points_y: list[float] = []
    ids: list[int] = []

    for id, point in waypoints_gs.waypoints.items():

        points_x.append(point.position.x)
        points_y.append(-point.position.y)
        ids.append(id)

        for visible_node_id in point.visible_nodes:
            visible_node = waypoints_gs.waypoints[visible_node_id]

            segments.append(
                [
                    (point.position.x, -point.position.y),
                    (visible_node.position.x, -visible_node.position.y),
                ]
            )

    # draw nodes
    plt.scatter(points_x, points_y, color="C2", s=5)  # type: ignore

    for x, y, id_ in zip(points_x, points_y, ids):
        plt.text(x, y, str(id_), fontsize=6, ha="left", va="bottom")  # type: ignore

    # draw visibility graph
    lc = LineCollection(segments, colors="C2", linewidths=0.5, alpha=0.15)
    plt.gca().add_collection(lc)


if __name__ == "__main__":

    gs = load_state("./scenes/experiment-s2.json")
    draw_terrains(gs)
    draw_waypoints(gs, InitiativeState.Faction.BLUE)
    draw_los(gs, unit_id=10)
    draw_los(gs, unit_id=11)
    plt.show()  # type: ignore
