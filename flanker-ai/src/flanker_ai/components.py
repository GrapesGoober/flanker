from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import InitiativeState, Vec2


@dataclass
class AiConfigComponent:

    @dataclass
    class WaypointsStateConfig:
        type: Literal["WaypointsStateConfig"]
        waypoint_coordinates: list[Vec2]
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

    StateConfigTypes = WaypointsStateConfig | UnabstractedStateConfig
    PolicyConfigTypes = RandomHeuristicPolicyConfig | ExpectimaxPolicyConfig

    faction: InitiativeState.Faction
    state_config: StateConfigTypes
    policy_config: PolicyConfigTypes
