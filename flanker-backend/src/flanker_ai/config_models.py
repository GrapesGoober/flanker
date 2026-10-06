from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import InitiativeState
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

    type ALL = Grid | HandDrawn | Random


class FilterConfig:

    @dataclass
    class LosSignaturesFilter:
        type: Literal["LosSignaturesFilter"]

    @dataclass
    class IngressLosSignaturesFilter:
        type: Literal["IngressLosSignaturesFilter"]

    type ALL = LosSignaturesFilter | IngressLosSignaturesFilter


class TranspositionScheme:

    @dataclass
    class RoundedPosition:
        type: Literal["RoundedPosition"]
        to_nearest: int

    @dataclass
    class RoundedRotation:
        type: Literal["RoundedRotation"]
        to_nearest: int

    type ALL = RoundedPosition | RoundedRotation


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
    transposition_schemes: list[TranspositionScheme.ALL]


class PolicyConfig:

    @dataclass
    class MctsPolicy:
        type: Literal["MctsPolicy"]
        max_iterations: int
        max_simulate_length: int
        simulation_policy: Literal["random", "rh"]

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


@dataclass
class AiConfigComponent:
    """
    Configures AI agent of either BLUE or RED with search policy and state.
    Supports search-based policy or heuristic rule-based policy.
    """

    config: SearchPolicyConfig | HeuristicPolicyConfig
    faction: InitiativeState.Faction
