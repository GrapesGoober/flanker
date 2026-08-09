from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

import matplotlib.pyplot as plt
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.common.ai_polytope_service import AiPolytopeService
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.utils.transform_utils import TransformUtils
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons, Slider
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# pyright: reportUnknownMemberType=false
# pyright: reportMissingTypeStubs=false


def main() -> None:
    gs = get_game_state(paths=["./scenes/visualize-polytope.json"])

    # Create a 3D figure and axis
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Draw terrains at z = 0 base plane
    draw_terrains(gs, ax)

    # Generate LOS polygons
    los_polytope = AiPolytopeService.get_los_polytope_fov_clipped(gs)
    poly3d_map: dict[tuple[Vec2, float], list[tuple[float, float, float]]] = {}
    for (key_vec, key_deg), polygon in los_polytope.items():
        z_val = key_vec.x  # Have it z-offset with x value
        poly3d_map[(key_vec, key_deg)] = [(v.x, v.y, z_val) for v in polygon]

    # Add LOS polygon slices to a collection
    initial_verts = poly3d_map[Vec2(10, 10), 0]
    los_collection = Poly3DCollection(
        [initial_verts],
        facecolors="none",  # Set to a color like "C0" if you want filled faces
        edgecolors=to_rgba("C0", alpha=0.5),
    )
    ax.add_collection(los_collection)

    # Config my rendering preferences
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 300)
    ax.set_zlim(0, 300)
    ax.invert_yaxis()
    ax.axis("off")

    # Slider for selecting the x and y vakyes
    x_slider_ax = fig.add_axes((0.30, 0.1, 0.60, 0.03))
    y_slider_ax = fig.add_axes((0.30, 0.06, 0.60, 0.03))
    deg_slider_ax = fig.add_axes((0.30, 0.02, 0.60, 0.03))
    x_values = [key_vec.x for (key_vec, _) in los_polytope.keys()]
    y_values = [key_vec.y for (key_vec, _) in los_polytope.keys()]
    deg_values = [key_deg for (_, key_deg) in los_polytope.keys()]
    x_slider = Slider(
        x_slider_ax,
        "X",
        valmin=x_values[0],
        valmax=x_values[-1],
        valinit=x_values[0],
        valstep=x_values,
    )
    y_slider = Slider(
        y_slider_ax,
        "Y",
        valmin=y_values[0],
        valmax=y_values[-1],
        valinit=y_values[0],
        valstep=y_values,
    )
    deg_slider = Slider(
        deg_slider_ax,
        "Degrees",
        valmin=deg_values[0],
        valmax=deg_values[-1],
        valinit=deg_values[0],
        valstep=deg_values,
    )

    # Checkbox to render all x values
    checkbox_ax = fig.add_axes((0.03, 0.04, 0.2, 0.08))
    checkbox_render_all_x = CheckButtons(
        checkbox_ax,
        ["Render all X"],
        [False],
    )

    # Redraw when slider is moved
    def update(_: Any) -> None:
        render_all_x = checkbox_render_all_x.get_status()[0]
        y_value = y_slider.val
        deg_value = deg_slider.val

        if not render_all_x:
            los_collection.set_verts(
                [poly3d_map[Vec2(x_slider.val, y_value), deg_value]]
            )
        else:
            vertices = [
                poly
                for (key_vec, key_deg), poly in poly3d_map.items()
                if key_vec.y == y_value
                if key_deg == deg_value
            ]
            los_collection.set_verts(vertices)

        fig.canvas.draw_idle()

    x_slider.on_changed(update)
    y_slider.on_changed(update)
    deg_slider.on_changed(update)
    checkbox_render_all_x.on_clicked(update)

    plt.tight_layout(pad=0)
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


def visualize_polygon_3d(
    ax: Axes,
    verts: list[Vec2],
    z_offset: float = 0.0,
    color: str = "C0",
    plot_alpha: float = 1.0,
    linestyle: str = "-",
) -> Line2D:
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [z_offset] * len(verts)

    return ax.plot(
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


if __name__ == "__main__":
    main()
