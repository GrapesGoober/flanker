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
from flanker_ai.states.common.ai_waypoints_initialize_service import (
    AiWaypointsInitializeService,
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
    draw_as_cone: bool = True,
) -> None:
    spotter_transform = gs.get_component(unit_id, components.Transform)
    polygon = LosSystem.get_los_polygon(
        gs=gs,
        spotter_pos=spotter_transform.position,
    )
    if draw_as_cone:
        polygon = LosSystem.apply_fov_to_polygon(
            polyline=polygon,
            center_point=spotter_transform.position,
            heading_degree=spotter_transform.degrees,
        )

    visualize_polygon(
        polygon,
        color=color,
        fill_alpha=0.1,
        plot_alpha=0.3,
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
        full_polygon = LosSystem.get_los_polygon(
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
    draw_initial: bool,
) -> None:

    if draw_initial:
        waypoints: list[Vec2] = []
        for _, conf in gs.query(AiConfigComponent):
            if conf.faction != faction:
                continue
            if conf.config.policy_type != "Minimax":
                continue
            if conf.config.state.type != "UnabstractedStateConfig":
                continue
            points_conf = conf.config.state.move_candidates.initial_points
            if points_conf.type != "GridConfig":
                continue
            waypoints = AiWaypointsInitializeService.get_grid_coordinates(
                gs=gs,
                spacing=points_conf.spacing,
                offset=points_conf.offset,
            )

        points_x = [waypoint.x for waypoint in waypoints]
        points_y = [waypoint.y for waypoint in waypoints]
        plt.scatter(  # type: ignore
            points_x,
            points_y,
            color="C0",
            marker="o",
            s=80,
        )

    agent = AiAgent.get_agent(gs, faction)

    assert isinstance(
        agent.rs, UnabstractedState
    ), "Method draw_move_candidates can only be used with unabstracted state"

    agent.rs.update_state(gs)

    move_candidates = agent.rs.move_candidates
    points_x = [coords.x for coords in move_candidates]
    points_y = [coords.y for coords in move_candidates]
    plt.scatter(  # type: ignore
        points_x,
        points_y,
        color="C1",
        marker="s",
        s=80,
    )

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


def visualize_expansion(gs: GameState) -> None:

    waypoints = [
        segment_a := Vec2(60, 120),
        segment_b := Vec2(230, 200),
        los_point := Vec2(130, 70),
    ]

    los_polygon = LosSystem.get_los_polygon(gs, los_point)
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
        ("C1", "^"): intersections,
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
            s=100,
            zorder=10,
        )


def visualize_pruning(gs: GameState) -> None:
    waypoints = [
        Vec2(66, 66),
        Vec2(66, 133),
        Vec2(66, 200),
        Vec2(150, 66),
        Vec2(150, 133),
        Vec2(150, 200),
        Vec2(233, 66),
        Vec2(233, 133),
        Vec2(233, 200),
    ]

    expanded_waypoints = AiPointsExpansionService.expand_waypoints_line_based(
        gs=gs,
        initial_waypoints=waypoints,
        tolerance=10,
    )
    expanded_waypoints_except_initial = [
        new_waypoint
        for new_waypoint in expanded_waypoints
        if new_waypoint not in waypoints
    ]

    flag_waypoints = [
        Vec2(66, 166),
        Vec2(100, 200),
        Vec2(200, 66),
        Vec2(233, 100),
    ]

    pruned_waypoints = AiPointsExpansionService.prune_waypoints_by_flags(
        gs=gs,
        waypoints=expanded_waypoints,
        flag_waypoints=flag_waypoints,
    )

    points_and_styles: dict[tuple[bool, str, str], list[Vec2]] = {
        (True, "C2", "s"): expanded_waypoints,
        (False, "C2", "s"): expanded_waypoints_except_initial,
        (True, "C1", "s"): pruned_waypoints,
        (False, "C0", "o"): waypoints,
        (False, "C1", "o"): flag_waypoints,
    }
    for (is_rendered, color, marker), points in points_and_styles.items():
        if not is_rendered:
            continue
        points_x = [coords.x for coords in points]
        points_y = [coords.y for coords in points]
        plt.scatter(  # type: ignore
            points_x,
            points_y,
            color=color,
            marker=marker,
            s=100,
            zorder=10,
        )


if __name__ == "__main__":

    gs = get_game_state(
        paths=[
            "./scenes/visualize-los.json"
            # "./scenes/experiment-settings.json",
            # "./scenes/experiment-scene-2.json",
            # "./scenes/experiment-blue-analysis.json",
        ]
    )

    # visualize_pruning(gs)
    # visualize_expansion(gs)

    screenshot = "./scripts/visualize-los.png"
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
    # draw_move_candidates(
    #     gs,
    #     InitiativeState.Faction.BLUE,
    #     draw_lines=False,
    #     draw_initial=True,
    # )

    # Draw LOS for each combat unit
    if True:
        for id, unit in gs.query(CombatUnit):
            if unit.faction == InitiativeState.Faction.BLUE:
                draw_combat_unit_los_cone(
                    gs,
                    unit_id=id,
                    color="C0",
                    linestyle="--",
                    draw_as_cone=True,
                )

            if unit.faction == InitiativeState.Faction.RED:
                draw_combat_unit_los_cone(
                    gs,
                    unit_id=id,
                    color="C1",
                    linestyle="--",
                    draw_as_cone=True,
                )

    # plt.axis("equal") # type: ignore
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.axis("off")  # type: ignore
    plt.axis((0, 300, 300, 0))  # type: ignore
    plt.savefig("visualize-los", dpi=300)  # type: ignore
    plt.show()  # type: ignore
