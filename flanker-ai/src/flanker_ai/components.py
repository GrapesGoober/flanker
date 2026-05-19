from dataclasses import dataclass, field

from flanker_ai.config_models import (
    ExpectimaxPolicyConfig,
    MinimaxPolicyConfig,
    RandomHeuristicPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_core.models.components import InitiativeState


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

    StateConfigTypes = WaypointsStateConfig | UnabstractedStateConfig
    PolicyConfigTypes = (
        RandomHeuristicPolicyConfig | ExpectimaxPolicyConfig | MinimaxPolicyConfig
    )

    faction: InitiativeState.Faction
    state_config: StateConfigTypes
    policy_config: PolicyConfigTypes
