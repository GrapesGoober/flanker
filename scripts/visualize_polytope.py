from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.transform_utils import TransformUtils
from matplotlib import pyplot as plt


def main() -> None:
    gs = get_game_state(paths=["./scenes/visualize-los.json"])
    plt.gca().invert_yaxis()

    draw_terrains(gs)

    draw_los(
        gs,
        spotter_pos=Vec2(10, 10),
        color="C0",
        linestyle="--",
    )

    # plt.axis("equal") # type: ignore
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.axis("off")  # type: ignore
    plt.axis((0, 300, 300, 0))  # type: ignore
    plt.show()  # type: ignore


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


def draw_los(
    gs: GameState,
    spotter_pos: Vec2,
    color: str = "C0",
    linestyle: str = "-",
) -> None:
    polygon = LosSystem.get_los_polygon(
        gs=gs,
        spotter_pos=spotter_pos,
    )
    visualize_polygon(
        polygon,
        color=color,
        fill_alpha=0.1,
        plot_alpha=0.3,
        linestyle=linestyle,
    )


if __name__ == "__main__":
    main()
