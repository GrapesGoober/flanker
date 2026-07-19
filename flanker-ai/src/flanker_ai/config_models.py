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
    class RandomConfig:
        type: Literal["Random"]
        count: int

    @dataclass
    class VoronoiConfig:
        type: Literal["VoronoiConfig"]

    @dataclass
    class LineBasedExpansionConfig:
        type: Literal["LineBased"]
        tolerance: float

    @dataclass
    class PolygonalExpansionConfig:
        type: Literal["Polygonal"]

    @dataclass
    class FlagPruneConfig:
        type: Literal["FlagPrune"]

    @dataclass
    class WeightsPruneConfig:
        type: Literal["WeightsPrune"]
        remaining_size: int

    initial_points: GridConfig | HandDrawnConfig | VoronoiConfig | RandomConfig
    use_combat_unit_positions: bool
    expansions: list[
        (
            LineBasedExpansionConfig
            | PolygonalExpansionConfig
            | FlagPruneConfig
            | WeightsPruneConfig
        )
    ]


@dataclass
class WaypointsStateConfig:
    type: Literal["WaypointsStateConfig"]
    waypoints: PointsConfig
    path_tolerance: float


@dataclass
class UnabstractedStateConfig:
    type: Literal["UnabstractedStateConfig"]
    move_candidates: PointsConfig
    divide_moves_per_unit: bool


@dataclass
class SearchPolicyConfig:
    policy_type: Literal["Minimax"] | Literal["Expectimax"] | Literal["MCTS"]
    state: WaypointsStateConfig | UnabstractedStateConfig


@dataclass
class HeuristicPolicyConfig:
    policy_type: Literal["RandomHeuristic"]
