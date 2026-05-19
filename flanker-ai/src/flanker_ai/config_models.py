from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import Vec2

# TODO: this is using string literal type discriminator
# Is this needed? Should it be removed? What cleaner options is available?


@dataclass
class WaypointsStateConfig:

    @dataclass
    class CoordinatesGridConfig:
        type: Literal["WaypointsCoordinatesGridConfig"]
        spacing: float
        offset: float

    @dataclass
    class HandDrawnConfig:
        type: Literal["WaypointsCoordinatesHandDrawnConfig"]
        waypoint_coordinates: list[Vec2]

    @dataclass
    class VoronoiConfig:
        type: Literal["WaypointsCoordinatesVoronoiConfig"]

    type: Literal["WaypointsStateConfig"]
    points: CoordinatesGridConfig | HandDrawnConfig | VoronoiConfig
    path_tolerance: float


@dataclass
class UnabstractedStateConfig:
    type: Literal["UnabstractedStateConfig"]


@dataclass
class SearchPolicyConfig:
    policy_type: Literal["Minimax"] | Literal["Expectimax"]
    state: WaypointsStateConfig | UnabstractedStateConfig


@dataclass
class HeuristicPolicyConfig:
    policy_type: Literal["RandomHeuristic"]
