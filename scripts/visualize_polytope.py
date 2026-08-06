from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

import matplotlib.pyplot as plt
from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.transform_utils import TransformUtils
from matplotlib.axes import Axes


def main() -> None:
    gs = get_game_state(paths=["./scenes/visualize-polytope.json"])

    # Create a 3D figure and axis
    fig = plt.figure()  # type: ignore
    ax = fig.add_subplot(111, projection="3d")

    # Draw terrains at z = 0 base plane
    draw_terrains(gs, ax)

    # Generate LOS polygons where z offset equals the x coordinate
    for x in range(10, 290, 10):
        draw_los(
            gs,
            spotter_pos=Vec2(x, 10),
            z_offset=float(x),
            ax=ax,
            color="C0",
            linestyle="-",
        )

    # Configure 3D space bounds to 300x300x300
    ax.set_xlim(0, 300)  # type: ignore
    ax.set_ylim(0, 300)  # type: ignore
    ax.set_zlim(0, 300)  # type: ignore

    # Invert Y-axis to match 2D screen coordinate conventions if desired
    ax.invert_yaxis()
    ax.axis("off")
    plt.tight_layout(pad=0)
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


def visualize_polygon_3d(
    ax: Axes,
    verts: list[Vec2],
    z_offset: float = 0.0,
    color: str = "C0",
    plot_alpha: float = 1.0,
    linestyle: str = "-",
) -> None:
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [z_offset] * len(verts)

    ax.plot(  # type: ignore
        xs,
        ys,
        zs,
        linestyle=linestyle,
        color=color,
        alpha=plot_alpha,
        linewidth=1.5,
    )


def draw_terrains(gs: GameState, ax: Axes) -> None:
    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = TransformUtils.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        visualize_polygon_3d(
            ax=ax,
            verts=vertices,
            z_offset=0.0,
            color="forestgreen",
            plot_alpha=1.0,
        )


def draw_los(
    gs: GameState,
    spotter_pos: Vec2,
    z_offset: float,
    ax: Axes,
    color: str = "C0",
    linestyle: str = "-",
) -> None:
    polygon = LosSystem.get_los_polygon(
        gs=gs,
        spotter_pos=spotter_pos,
    )
    visualize_polygon_3d(
        ax=ax,
        verts=polygon,
        z_offset=z_offset,
        color=color,
        plot_alpha=0.3,
        linestyle=linestyle,
    )


if __name__ == "__main__":
    main()
