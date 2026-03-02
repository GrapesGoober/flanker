from dataclasses import dataclass, field
from typing import Literal

from flanker_core.models.components import InitiativeState, Vec2


@dataclass
class AiStallCountComponent:
    stall_counter: dict[InitiativeState.Faction, int] = field(
        default_factory=lambda: {
            InitiativeState.Faction.BLUE: 0,
            InitiativeState.Faction.RED: 0,
        }
    )


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

    @dataclass
    class MinimaxPolicyConfig:
        type: Literal["MinimaxPolicyConfig"]
        ...

    StateConfigTypes = WaypointsStateConfig | UnabstractedStateConfig
    PolicyConfigTypes = (
        RandomHeuristicPolicyConfig | ExpectimaxPolicyConfig | MinimaxPolicyConfig
    )

    faction: InitiativeState.Faction
    state_config: StateConfigTypes
    policy_config: PolicyConfigTypes
