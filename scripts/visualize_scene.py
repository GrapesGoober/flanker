from dataclasses import is_dataclass
from inspect import isclass
from itertools import product
from typing import Any
from uuid import UUID

import matplotlib.image as mpimg
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import SearchPolicyConfig
from flanker_ai.states.common.ai_points_initialize_service import (
    AiPointsInitializeService,
)
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_graph import WaypointsGraph
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.polygon_utils import PolygonUtils
from flanker_core.utils.transform_utils import TransformUtils
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

# pyright: reportUnknownMemberType=false


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
        vertices = TransformUtils.apply(terrain.vertices, transform)
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
        polygon = PolygonUtils.clip_by_fov_cone(
            polyline=polygon,
            center_point=spotter_transform.position,
            heading_degree=spotter_transform.degrees,
        )

    visualize_polygon(
        polygon,
        color=color,
        fill_alpha=0.05,
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

    print("Drawing waypoints...")

    segments: list[list[tuple[float, float]]] = []
    points_x: list[float] = []
    points_y: list[float] = []
    ids: list[int] = []

    waypoints = WaypointsGraph.get_waypoints(waypoints_state.gs)

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

    draw_graph(
        points_x,
        points_y,
        segments,
        color="C0",
        linewidth=1,
        alpha=0.05,
    )


# TODO: refactor this to handle both unabstracted and waypoints state.
# Do this by using the method get_actions(), and visualize THAT
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
            if type(conf.config) != SearchPolicyConfig:
                continue
            if conf.config.policy.type != "MinimaxPolicy":
                continue
            if conf.config.state.type != "UnabstractedStateConfig":
                continue
            points_conf = conf.config.state.move_candidates.initial_points
            if points_conf.type != "GridConfig":
                continue
            waypoints = AiPointsInitializeService.get_grid_coordinates(
                gs=gs,
                spacing=points_conf.spacing,
                offset=points_conf.offset,
            )

        points_x = [waypoint.x for waypoint in waypoints]
        points_y = [waypoint.y for waypoint in waypoints]
        plt.scatter(
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
    plt.scatter(
        points_x,
        points_y,
        color="C1",
        marker="s",
        s=80,
    )

    for point in move_candidates:
        plt.text(
            point.x,
            point.y,
            f"({round(point.x, 2)}, {round(point.y, 2)})",
            fontsize=8,
            ha="left",
            va="bottom",
        )

        signature: list[str] = []
        for _, _, transform in gs.query(CombatUnit, Transform):
            has_los = LosSystem.has_los(
                gs,
                spotter_pos=transform.position,
                target_pos=point,
            )
            signature.append("1" if has_los else "0")

        plt.text(
            point.x,
            point.y,
            f"({",".join(signature)})",
            fontsize=8,
            ha="left",
            va="top",
        )

    if draw_lines:
        segments = [
            ((p1.x, p1.y), (p2.x, p2.y))
            for p1, p2 in product(move_candidates, repeat=2)
        ]
        lc = LineCollection(segments, colors="C0", linewidths=1, alpha=0.1)
        plt.gca().add_collection(lc)


if __name__ == "__main__":

    gs = get_game_state(
        paths=[
            # "./scenes/visualize-los.json"
            "./scenes/experiment-settings.json",
            "./scenes/experiment-scene-2.json",
            # "./scenes/experiment-blue-analysis.json",
            "./scenes/experiment-blue-waypoints.json",
        ]
    )

    screenshot = None  # "./scripts/screenshots/experiment-scene-2.png"
    if screenshot:
        img = mpimg.imread(screenshot)  # type: ignore
        plt.imshow(  # type: ignore
            img,  # type: ignore
            extent=[0, 300, 300, 0],  # type: ignore
        )
    else:
        plt.gca().invert_yaxis()

    # draw_terrains(gs)
    draw_waypoints(gs, InitiativeState.Faction.BLUE, draw_ids=True)
    # draw_move_candidates(
    #     gs,
    #     InitiativeState.Faction.BLUE,
    #     draw_lines=False,
    #     draw_initial=False,
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
                    draw_as_cone=False,
                )

            if unit.faction == InitiativeState.Faction.RED:
                draw_combat_unit_los_cone(
                    gs,
                    unit_id=id,
                    color="C1",
                    linestyle="--",
                    draw_as_cone=False,
                )

    # plt.axis("equal")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.axis("off")
    plt.axis((0, 300, 300, 0))
    # plt.savefig("./scripts/outputs/visualize-los", dpi=300)
    plt.show()
