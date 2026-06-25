from dataclasses import is_dataclass
from inspect import isclass
from itertools import product
from typing import Any
from uuid import UUID

import matplotlib.image as mpimg
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
)
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointsGraphSystem
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.register_systems import register_systems
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection


def get_game_state(
    paths: list[str],
) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    entities: dict[UUID, Any] = {}
    for path in paths:
        with open(path, "r") as f:
            entities.update(
                Serializer.deserialize(
                    json_data=f.read(),
                    component_types=component_types,
                )
            )

    gs = GameState.load(entities)
    register_systems(gs)
    return gs


def visualize_polygon(
    verts: list[Vec2],
    color: str = "C0",
    fill_alpha: float = 0,
    plot_alpha: float = 1,
    linestyle: str = "-",
) -> None:
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]

    # plt.scatter(xs, ys, color=color)  # type: ignore
    plt.fill(xs, ys, color=color, alpha=fill_alpha)  # type: ignore
    plt.plot(  # type: ignore
        xs,
        ys,
        linestyle=linestyle,
        color=color,
        alpha=plot_alpha,
        linewidth=3.0,
    )
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
    linestyle: str = "-",
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
        plot_alpha=0.5,
        linestyle=linestyle,
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

    waypoints = waypoints_system.get_waypoints(waypoints_state.gs)

    for id, point in waypoints.items():

        if draw_ids:
            plt.text(  # type: ignore
                point.position.x,
                point.position.y,
                str(id),
            )

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


def draw_move_candidates(
    gs: GameState,
    faction: InitiativeState.Faction,
    draw_lines: bool,
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

    # for point in move_candidates:
    #     plt.text(  # type: ignore
    #         point.x,
    #         point.y,
    #         str(f"({round(point.x, 2)}, {round(point.y, 2)})"),
    #         fontsize=8,
    #         ha="left",
    #         va="bottom",
    #     )

    if draw_lines:
        segments = [
            ((p1.x, p1.y), (p2.x, p2.y))
            for p1, p2 in product(move_candidates, repeat=2)
        ]
        lc = LineCollection(segments, colors="C0", linewidths=1, alpha=0.1)
        plt.gca().add_collection(lc)


def is_colinear(previous_points: list[Vec2], new_point: Vec2) -> bool:
    if len(previous_points) >= 2:
        a = previous_points[-2]
        b = previous_points[-1]
        c = new_point
        ab = b - a
        ac = c - a
        cross = ab.cross(ac)
        if abs(cross) < 1e-9:
            return True

    return False


def visualize_expansion() -> None:

    waypoints = [
        segment_a := Vec2(60, 120),
        segment_b := Vec2(230, 200),
        los_point := Vec2(130, 70),
    ]

    los_system = gs.get(LosSystem)
    los_polygon = los_system.get_los_polygon(gs, los_point)
    visualize_polygon(
        los_polygon,
        color=f"C0",
        fill_alpha=0.2,
        plot_alpha=0.3,
        linestyle="--",
    )

    waypoints = AiPointsExpansionService.expand_waypoints_line_based(
        gs=gs,
        initial_waypoints=waypoints,
        tolerance=10,
    )

    plt.scatter(segment_a.x, segment_a.y, color=f"C0", s=80)  # type: ignore
    plt.scatter(segment_b.x, segment_b.y, color=f"C0", s=80)  # type: ignore
    plt.scatter(los_point.x, los_point.y, color=f"C0", s=80)  # type: ignore

    intersections: list[Vec2] = []
    all_polygons: list[list[Vec2]] = []
    for _, transform, terrain in gs.query(Transform, TerrainFeature):
        vertices = LinearTransform.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        all_polygons.append(vertices)
    all_polygons.append(los_polygon)
    for polygon in all_polygons:
        intersects = IntersectGetter.get_intersects(
            line=(segment_a, segment_b),
            polyline=polygon,
        )
        intersections += list(intersects)

    plt.plot(  # type: ignore
        [p.x for p in (segment_a, segment_b)],
        [p.y for p in (segment_a, segment_b)],
        linestyle="-",
        color=f"C0",
        alpha=1,
        linewidth=3.0,
    )

    new_expanded_points = [
        waypoint
        for waypoint in waypoints
        if is_colinear([segment_a, segment_b], waypoint)
        and waypoint != segment_a
        and waypoint != segment_b
    ]

    points_and_styles: dict[tuple[str, str], list[Vec2]] = {
        ("C1", "X"): intersections,
        ("C2", "s"): new_expanded_points,
    }

    for (color, marker), points in points_and_styles.items():
        points_x = [coords.x for coords in points]
        points_y = [coords.y for coords in points]
        plt.scatter(  # type: ignore
            points_x,
            points_y,
            color=color,
            marker=marker,
            s=80,
            zorder=10,
        )


if __name__ == "__main__":

    gs = get_game_state(
        paths=[
            "./scenes/visualize-expansion.json"
            # "./scenes/experiment-settings.json",
            # "./scenes/experiment-scene-1.json",
            # "./scenes/experiment-blue-analysis.json",
        ]
    )

    visualize_expansion()

    screenshot = "./scripts/visualize-expansion.png"
    if screenshot:
        img = mpimg.imread(screenshot)  # type: ignore
        plt.imshow(  # type: ignore
            img,  # type: ignore
            extent=[0, 300, 300, 0],  # type: ignore
        )
    else:
        plt.gca().invert_yaxis()

    # draw_terrains(gs)
    # draw_waypoints(gs, InitiativeState.Faction.BLUE, draw_ids=True)
    # draw_move_candidates(gs, InitiativeState.Faction.BLUE, draw_lines=False)

    # Draw LOS for each combat unit
    for id, unit in gs.query(CombatUnit):
        if unit.faction == InitiativeState.Faction.BLUE:
            draw_combat_unit_los_cone(
                gs,
                unit_id=id,
                color="C0",
                linestyle="--",
            )

        if unit.faction == InitiativeState.Faction.RED:
            draw_combat_unit_los_cone(
                gs,
                unit_id=id,
                color="C1",
                linestyle="--",
            )

    # plt.axis("equal") # type: ignore
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.axis("off")  # type: ignore
    plt.axis((33, 266, 233, 33))  # type: ignore
    plt.savefig("methodology-expansion-3.png", dpi=300)  # type: ignore
    plt.show()  # type: ignore
