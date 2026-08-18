from dataclasses import dataclass
from typing import Literal

from flanker_core.models.vec2 import Vec2

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
    class FlagPruneConfig:
        type: Literal["FlagPrune"]

    initial_points: GridConfig | HandDrawnConfig | RandomConfig
    expansions: list[FlagPruneConfig]


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


class PolicyConfig:

    @dataclass
    class MctsPolicy:
        type: Literal["MctsPolicy"]
        max_iterations: int
        max_simulate_length: int
        simulation_policy: Literal["random"] | Literal["rh"]
        score_factor: int

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
