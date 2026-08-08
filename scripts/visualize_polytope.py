from dataclasses import is_dataclass
from inspect import isclass
from itertools import pairwise
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
from matplotlib.widgets import CheckButtons, Slider


def main() -> None:
    gs = get_game_state(paths=["./scenes/visualize-polytope.json"])

    # Create a 3D figure and axis
    fig = plt.figure()  # type: ignore
    ax = fig.add_subplot(111, projection="3d")

    # Draw terrains at z = 0 base plane
    draw_terrains(gs, ax)

    # Generate LOS polygons where z offset equals the x coordinate
    los_polygons: dict[float, list[Vec2]] = {}
    for x in range(10, 290, 10):
        los_polygons[x] = LosSystem.get_los_polygon(gs, Vec2(x, 10))

    los_plotlines = draw_los_polytope(los_polygons, ax, color="C0")

    x_markers = get_discontinuous_x_values(los_polygons)
    ax.scatter3D(  # type: ignore
        xs=x_markers,
        ys=10,
        zs=0,
    )

    # Configure 3D space bounds to 300x300x300
    ax.set_xlim(0, 300)  # type: ignore
    ax.set_ylim(0, 300)  # type: ignore
    ax.set_zlim(0, 300)  # type: ignore

    # Invert Y-axis to match 2D screen coordinate conventions if desired
    ax.invert_yaxis()
    ax.axis("off")

    # --- UI ---

    # Slider for selecting the X value
    slider_ax = fig.add_axes([0.20, 0.04, 0.60, 0.03])  # type: ignore
    x_values = list(los_polygons.keys())
    slider = Slider(
        slider_ax,  # type: ignore
        "X",
        valmin=x_values[0],
        valmax=x_values[-1],
        valinit=x_values[0],
        valstep=x_values,
    )

    # Checkbox for all-at-once mode
    checkbox_ax = fig.add_axes([0.02, 0.04, 0.12, 0.08])  # type: ignore
    checkbox = CheckButtons(
        checkbox_ax,  # type: ignore
        ["Render all"],
        [True],
    )

    def update(_: Any) -> None:
        render_all = checkbox.get_status()[0]

        if render_all:
            # Show every polygon
            for line in los_plotlines:
                line.set_visible(True)
        else:
            # Show only the polygon corresponding to the slider X
            selected_x = slider.val

            for x, line in zip(x_values, los_plotlines):
                line.set_visible(x == selected_x)

        fig.canvas.draw_idle()  # type: ignore

    slider.on_changed(update)
    checkbox.on_clicked(update)

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
) -> Any:
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [z_offset] * len(verts)

    return ax.plot(  # type: ignore
        xs,
        ys,
        zs,
        linestyle=linestyle,
        color=color,
        alpha=plot_alpha,
        linewidth=1.5,
    )[0]


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


def draw_los_polytope(
    los_polygons: dict[float, list[Vec2]],
    ax: Axes,
    color: str = "C0",
) -> list[Any]:
    lines: list[Any] = []

    for z_offset, polygon in los_polygons.items():
        line = visualize_polygon_3d(
            ax=ax,
            verts=polygon,
            z_offset=z_offset,
            color=color,
            plot_alpha=0.3,
        )
        lines.append(line)

    return lines


def get_discontinuous_x_values(
    los_polygons: dict[float, list[Vec2]],
) -> list[float]:
    discontinuous_x: list[float] = []
    for left, right in pairwise(los_polygons.items()):
        _, polygon_left = left
        z_offset_right, polygon_right = right
        if len(polygon_left) != len(polygon_right):
            discontinuous_x.append(z_offset_right)

    return discontinuous_x


if __name__ == "__main__":
    main()
