from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import Vec2

# TODO: this is using string literal type discriminator
# Is this needed? Should it be removed? What cleaner options are available?
# Yo, check this out https://pydantic.dev/docs/validation/latest/concepts/unions/.


@dataclass
class PointsConfig:
    @dataclass
    class GridConfig:
        type: Literal["GridConfig"]
        spacing: float
        offset: float

    @dataclass
    class HandDrawnConfig:
        type: Literal["HandDrawnConfig"]
        points: list[Vec2]

    @dataclass
    class VoronoiConfig:
        type: Literal["VoronoiConfig"]

    @dataclass
    class ExpansionConfig:
        type: Literal["LineBased"] | Literal["Polygonal"]
        iterations: int
        prune_iterations: int

    initial_points: GridConfig | HandDrawnConfig | VoronoiConfig
    expansion: ExpansionConfig | None = None


@dataclass
class WaypointsStateConfig:
    type: Literal["WaypointsStateConfig"]
    waypoints: PointsConfig
    path_tolerance: float


@dataclass
class UnabstractedStateConfig:
    type: Literal["UnabstractedStateConfig"]
    move_candidates: PointsConfig | Literal["RandomMoves"]


@dataclass
class SearchPolicyConfig:
    policy_type: Literal["Minimax"] | Literal["Expectimax"]
    state: WaypointsStateConfig | UnabstractedStateConfig


@dataclass
class HeuristicPolicyConfig:
    policy_type: Literal["RandomHeuristic"]
