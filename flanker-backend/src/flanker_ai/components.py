from dataclasses import dataclass

from flanker_ai.config_models import HeuristicPolicyConfig, SearchPolicyConfig
from flanker_core.models.components import InitiativeState


@dataclass
class AiConfigComponent:
    """
    Configures AI agent of either BLUE or RED with search policy and state.
    Supports search-based policy or heuristic rule-based policy.
    """

    config: SearchPolicyConfig | HeuristicPolicyConfig
    faction: InitiativeState.Faction
