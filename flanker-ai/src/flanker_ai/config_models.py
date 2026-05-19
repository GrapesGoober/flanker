from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import Vec2


@dataclass
class WaypointsCoordinatesGridConfig:
    type: Literal["WaypointsCoordinatesGridConfig"]
    spacing: float
    offset: float


@dataclass
class WaypointsCoordinatesHandDrawnConfig:
    type: Literal["WaypointsCoordinatesHandDrawnConfig"]
    waypoint_coordinates: list[Vec2]


@dataclass
class WaypointsCoordinatesVoronoiConfig:
    type: Literal["WaypointsCoordinatesVoronoiConfig"]


@dataclass
class WaypointsStateConfig:
    type: Literal["WaypointsStateConfig"]
    coordinates: (
        WaypointsCoordinatesGridConfig
        | WaypointsCoordinatesHandDrawnConfig
        | WaypointsCoordinatesVoronoiConfig
    )
    path_tolerance: float


@dataclass
class UnabstractedStateConfig:
    type: Literal["UnabstractedStateConfig"]
    ...


@dataclass
class RandomHeuristicPolicyConfig:
    type: Literal["RandomHeuristicPolicyConfig"]
    ...


@dataclass
class ExpectimaxPolicyConfig:
    type: Literal["ExpectimaxPolicyConfig"]
    ...


@dataclass
class MinimaxPolicyConfig:
    type: Literal["MinimaxPolicyConfig"]
    ...
