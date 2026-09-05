from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

import matplotlib.image as mpimg
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.waypoints.waypoints_graph import WaypointsGraph
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.actions import MoveAction
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.polygon_utils import PolygonUtils
from flanker_core.utils.transform_utils import TransformUtils
from matplotlib import pyplot as plt

# pyright: reportUnknownMemberType=false


def main() -> None:

    gs = get_game_state(
        paths=[
            # "./scenes/visualize-los.json"
            "./scenes/experiment-settings.json",
            "./scenes/experiment-scene-2.json",
            # "./scenes/experiment-blue-analysis.json",
            "./scenes/experiment-blue-waypoints.json",
        ]
    )

    screenshot = "./scripts/screenshots/experiment-scene-2.png"
    if screenshot:
        img = mpimg.imread(screenshot)  # type: ignore
        plt.imshow(  # type: ignore
            img,  # type: ignore
            extent=[0, 300, 300, 0],  # type: ignore
        )
    else:
        plt.gca().invert_yaxis()

    # draw_terrains(gs)
    draw_waypoints(gs, InitiativeState.Faction.BLUE, draw_ids=True, draw_path=(65, 22))
    # draw_move_candidates(gs, InitiativeState.Faction.BLUE)

    # Draw LOS for each combat unit
    if False:
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
    plt.savefig("./scripts/outputs/visualize-waypoints", dpi=300)
    plt.show()


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


def draw_waypoints(
    gs: GameState,
    faction: InitiativeState.Faction,
    draw_path: tuple[int, int],
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

    plt.scatter(points_x, points_y, color="C0", s=40)

    if draw_path:
        xs: list[float] = []
        ys: list[float] = []
        move_from, move_to = draw_path
        path_nodes = waypoints[move_from].movable_paths[move_to]
        for path_node in path_nodes:
            position = waypoints[path_node].position
            xs.append(position.x)
            ys.append(position.y)
        plt.plot(xs, ys, color="C2", linewidth=2)
        direct_path_xs = [
            waypoints[move_from].position.x,
            waypoints[move_to].position.x,
        ]
        direct_path_ys = [
            waypoints[move_from].position.y,
            waypoints[move_to].position.y,
        ]
        plt.plot(direct_path_xs, direct_path_ys, color="C3", linewidth=2)


def draw_move_candidates(
    gs: GameState,
    faction: InitiativeState.Faction,
) -> None:

    agent = AiAgent.get_agent(gs, faction)
    agent.rs.update_state(gs)

    actions = [a for a in agent.rs.get_actions() if isinstance(a, MoveAction)]
    unit_id = actions[0].unit_id if actions else None
    moves: list[Vec2] = [a.to for a in actions if a.unit_id == unit_id]

    points_x = [v.x for v in moves]
    points_y = [v.y for v in moves]
    plt.scatter(points_x, points_y, color="C1", marker="s", s=60)  # type: ignore


if __name__ == "__main__":
    main()
