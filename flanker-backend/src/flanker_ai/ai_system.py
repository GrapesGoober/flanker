from dataclasses import dataclass

from flanker_ai.agents.ai_random_heuristic_agent import AiRandomHeuristicAgent
from flanker_ai.agents.ai_search_agent import AiSearchAgent
from flanker_ai.config_models import (
    AiConfigComponent,
    HeuristicPolicyConfig,
    SearchPolicyConfig,
)
from flanker_ai.search_policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: AiSearchAgent | AiRandomHeuristicAgent


class AiSystem:

    @dataclass
    class ActionResult:
        faction: InitiativeState.Faction
        action: Action
        result: ActionResult
        policy_log: AiSearchLog | None

    @staticmethod
    def perform_action(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> ActionResult | None:

        config_component: AiConfigComponent | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction == faction:
                config_component = component
                break
        if config_component == None:
            raise ValueError(f"{AiConfigComponent} not found")

        # TODO: each agent should have its own result models, even private,
        # which is then mapped to AI system's result models. This keeps it
        # nice and decoupled.
        match config_component.config:
            case HeuristicPolicyConfig():
                result = AiRandomHeuristicAgent.perform_action(gs)
                if result is None:
                    return None
                return AiSystem.ActionResult(
                    faction=faction,
                    action=result.action,
                    result=result.result,
                    policy_log=None,
                )
            case SearchPolicyConfig():
                result = AiSearchAgent.perform_action(
                    gs=gs,
                    config=config_component.config,
                )
                if result is None:
                    return None
                return AiSystem.ActionResult(
                    faction=faction,
                    action=result.action,
                    result=result.result,
                    policy_log=result.search_log,
                )
