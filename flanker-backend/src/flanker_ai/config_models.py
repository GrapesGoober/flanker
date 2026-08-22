from dataclasses import dataclass
from typing import Literal

from flanker_core.models.vec2 import Vec2


class PointsConfig:
    @dataclass
    class Grid:
        type: Literal["GridConfig"]
        spacing: float
        offset: float

    @dataclass
    class HandDrawn:
        type: Literal["HandDrawnConfig"]
        points: list[Vec2]

    @dataclass
    class Random:
        type: Literal["Random"]
        count: int

    ALL = Grid | HandDrawn | Random


class FilterConfig:

    @dataclass
    class LosSignaturesFilter:
        type: Literal["LosSignaturesFilter"]

    @dataclass
    class IngressLosSignaturesFilter:
        type: Literal["IngressLosSignaturesFilter"]

    ALL = LosSignaturesFilter | IngressLosSignaturesFilter


@dataclass
class WaypointsStateConfig:
    type: Literal["WaypointsStateConfig"]
    waypoints: PointsConfig.ALL
    move_candidates_filter: list[FilterConfig.ALL]
    path_tolerance: float


@dataclass
class UnabstractedStateConfig:
    type: Literal["UnabstractedStateConfig"]
    move_candidates_pool: PointsConfig.ALL
    move_candidates_filter: list[FilterConfig.ALL]
    divide_moves_per_unit: bool


class PolicyConfig:

    @dataclass
    class MctsPolicy:
        type: Literal["MctsPolicy"]
        max_iterations: int
        max_simulate_length: int
        simulation_policy: Literal["random"] | Literal["rh"]

    @dataclass
    class MinimaxPolicy:
        type: Literal["MinimaxPolicy"]
        depth: int

    @dataclass
    class ExpectimaxPolicy:
        type: Literal["ExpectimaxPolicy"]
        depth: int

    @dataclass
    class RandomHeuristicPolicy:
        type: Literal["RandomHeuristicPolicy"]


@dataclass
class SearchPolicyConfig:
    policy: (
        PolicyConfig.MinimaxPolicy
        | PolicyConfig.ExpectimaxPolicy
        | PolicyConfig.MctsPolicy
    )
    state: WaypointsStateConfig | UnabstractedStateConfig


@dataclass
class HeuristicPolicyConfig:
    policy: PolicyConfig.RandomHeuristicPolicy
