from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

import matplotlib
import pandas as pd
from flanker_ai.components import AiConfigComponent
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
from matplotlib.colors import to_rgba
from plotnine import (
    aes,
    coord_fixed,
    geom_polygon,
    ggplot,
    scale_y_reverse,
    theme_matplotlib,
)


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

    matplotlib.use("tkagg")
    plot = (
        ggplot()
        # Inverse y (positive y goes downwards)
        + scale_y_reverse()
        # ylim must count down to work with  scale_y_reverse
        + coord_fixed(ratio=1, xlim=(0, 300), ylim=(300, 0))
        + theme_matplotlib()
    )

    plot = draw_terrains(plot, gs)

    draw_as_cone = True
    for _, unit, transform in gs.query(CombatUnit, Transform):
        polygon = LosSystem.get_los_polygon(
            gs=gs,
            spotter_pos=transform.position,
        )
        if draw_as_cone:
            polygon = PolygonUtils.clip_by_fov_cone(
                polyline=polygon,
                center_point=transform.position,
                heading_degree=transform.degrees,
            )
        match unit.faction:
            case InitiativeState.Faction.BLUE:
                plot += get_polygon(
                    polygon,
                    color="lightblue",
                    fill_alpha=0.05,
                    plot_alpha=0.3,
                )
            case InitiativeState.Faction.RED:
                plot += get_polygon(
                    polygon,
                    color="orange",
                    fill_alpha=0.05,
                    plot_alpha=0.3,
                )
    plot.show()


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


def get_polygon(
    verts: list[Vec2],
    color: str = "C0",
    fill_alpha: float = 0,
    plot_alpha: float = 1,
    linewidth: int = 1,
) -> geom_polygon:
    return geom_polygon(
        aes("x", "y"),
        pd.DataFrame(
            {
                "x": [v.x for v in verts],
                "y": [v.y for v in verts],
            }
        ),
        color=to_rgba(color, plot_alpha),
        fill=color,
        alpha=fill_alpha,
        size=linewidth,
    )


def draw_terrains(
    plot: ggplot,
    gs: GameState,
) -> ggplot:
    newplot = plot
    for _, terrain, transform in gs.query(
        components.TerrainFeature,
        components.Transform,
    ):
        vertices = TransformUtils.apply(terrain.vertices, transform)
        if terrain.is_closed_loop:
            vertices.append(vertices[0])
        newplot += get_polygon(
            vertices,
            color="forestgreen",
            fill_alpha=0.1,
            plot_alpha=0.2,
        )
    return newplot


if __name__ == "__main__":
    main()
