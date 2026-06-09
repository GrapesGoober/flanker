from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

import matplotlib.image as mpimg
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointsGraphSystem
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import CombatUnit, InitiativeState
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.register_systems import register_systems
from flanker_core.utils.linear_transform import LinearTransform
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection


def load_state(path: str) -> GameState:

    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities)

    register_systems(gs)
    return gs


def visualize_polygon(
    verts: list[Vec2],
    color: str = "C0",
    fill_alpha: float = 0,
    plot_alpha: float = 1,
) -> None:
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]

    # plt.scatter(xs, ys, color=color)  # type: ignore
    plt.fill(xs, ys, color=color, alpha=fill_alpha)  # type: ignore
    plt.plot(xs, ys, linestyle="-", color=color, alpha=plot_alpha)  # type: ignore
    plt.axis("equal")  # type: ignore


def draw_terrains(gs: GameState) -> None:

    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = LinearTransform.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        visualize_polygon(
            vertices,
            color="forestgreen",
            fill_alpha=0,
            plot_alpha=0.2,
        )


def draw_combat_unit_los_cone(
    gs: GameState,
    unit_id: UUID,
    color: str = "C0",
) -> None:
    los_system = gs.get(LosSystem)

    spotter_transform = gs.get_component(unit_id, components.Transform)
    full_polygon = los_system.get_los_polygon(
        gs=gs,
        spotter_pos=spotter_transform.position,
    )
    los_polygon = los_system.apply_fov_to_polygon(
        polyline=full_polygon,
        center_point=spotter_transform.position,
        heading_degree=spotter_transform.degrees,
    )

    visualize_polygon(
        los_polygon,
        color=color,
        fill_alpha=0.2,
        plot_alpha=0.1,
    )


def draw_graph(
    points_x: list[float],
    points_y: list[float],
    segments: list[list[tuple[float, float]]],
    color: str,
    linewidth: float,
    alpha: float,
) -> None:

    # draw nodes
    plt.scatter(points_x, points_y, color=color, s=40)  # type: ignore

    # Draw ID
    # for x, y, id_ in zip(points_x, points_y, ids):
    #     plt.text(x, y, str(id_), fontsize=6, ha="left", va="bottom")  # type: ignore

    # draw visibility graph
    lc = LineCollection(segments, colors=color, linewidths=linewidth, alpha=alpha)
    plt.gca().add_collection(lc)


def draw_waypoints(
    gs: GameState,
    faction: InitiativeState.Faction,
    draw_ids: bool = False,
) -> None:

    print("Creating waypoints...")

    agent = AiAgent.get_agent(gs, faction)
    waypoints_state = agent.rs
    assert isinstance(
        waypoints_state, WaypointsState
    ), "Configured agent's state representation must be waypoints state."

    waypoints_state.update_state(gs)
    waypoints_system = waypoints_state.gs.get(WaypointsGraphSystem)
    los_system = gs.get(LosSystem)

    print("Drawing waypoints...")

    segments: list[list[tuple[float, float]]] = []
    points_x: list[float] = []
    points_y: list[float] = []
    ids: list[int] = []

    accented_segments: list[list[tuple[float, float]]] = []
    accented_points_x: list[float] = []
    accented_points_y: list[float] = []
    accented_ids: list[int] = []

    waypoints = waypoints_system.get_waypoints(waypoints_state.gs)

    for id, point in waypoints.items():

        if draw_ids:
            plt.text(  # type: ignore
                point.position.x,
                point.position.y,
                str(id),
            )

        if id in accented_ids:
            accented_points_x.append(point.position.x)
            accented_points_y.append(point.position.y)

            for visible_node_id in point.visible_nodes:
                visible_node = waypoints[visible_node_id]

                accented_segments.append(
                    [
                        (point.position.x, point.position.y),
                        (visible_node.position.x, visible_node.position.y),
                    ]
                )
            continue
        points_x.append(point.position.x)
        points_y.append(point.position.y)
        ids.append(id)

        for visible_node_id in point.visible_nodes:
            visible_node = waypoints[visible_node_id]

            segments.append(
                [
                    (point.position.x, point.position.y),
                    (visible_node.position.x, visible_node.position.y),
                ]
            )

        # Draw LOS polygon for each waypoint
        full_polygon = los_system.get_los_polygon(
            gs=gs,
            spotter_pos=point.position,
        )
        visualize_polygon(full_polygon, color="C0", fill_alpha=0.02, plot_alpha=0.05)

    # draw_graph(
    #     points_x,
    #     points_y,
    #     segments,
    #     color="C0",
    #     linewidth=1,
    #     alpha=0.05,
    # )
    # draw_graph(
    #     accented_points_x,
    #     accented_points_y,
    #     accented_segments,
    #     color="C1",
    #     linewidth=2,
    #     alpha=0.3,
    # )


def draw_move_candidates(
    gs: GameState,
    faction: InitiativeState.Faction,
) -> None:
    agent = AiAgent.get_agent(gs, faction)

    assert isinstance(
        agent.rs, UnabstractedState
    ), "Method draw_move_candidates can only be used with unabstracted state"

    agent.rs.update_state(gs)

    move_candidates = agent.rs.move_candidates
    points_x = [coords.x for coords in move_candidates]
    points_y = [coords.y for coords in move_candidates]

    plt.scatter(points_x, points_y, color="C0", s=40)  # type: ignore


if __name__ == "__main__":

    gs = load_state("./scenes/experiment-grid-1.json")

    screenshot = None  # "./scripts/experiment-template.png"
    if screenshot:
        img = mpimg.imread(screenshot)  # type: ignore
        plt.imshow(  # type: ignore
            img,  # type: ignore
            extent=[0, 300, 300, 0],  # type: ignore
        )
    else:
        plt.gca().invert_yaxis()

    draw_terrains(gs)
    # draw_waypoints(gs, InitiativeState.Faction.BLUE, draw_ids=True)
    draw_move_candidates(gs, InitiativeState.Faction.BLUE)

    # Draw LOS for each combat unit
    for id, unit in gs.query(CombatUnit):
        if unit.faction == InitiativeState.Faction.BLUE:
            draw_combat_unit_los_cone(gs, unit_id=id, color="C0")

        if unit.faction == InitiativeState.Faction.RED:
            draw_combat_unit_los_cone(gs, unit_id=id, color="C1")

    plt.axis("equal")  # type: ignore
    plt.show()  # type: ignore
