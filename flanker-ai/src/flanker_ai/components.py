from dataclasses import dataclass, field

from flanker_ai.config_models import HeuristicPolicyConfig, SearchPolicyConfig
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
    """Configures that AI agent of that faction with policy and state."""

    config: SearchPolicyConfig | HeuristicPolicyConfig
    faction: InitiativeState.Faction
