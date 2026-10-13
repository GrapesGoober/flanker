from dataclasses import dataclass
from time import perf_counter

from flanker_ai.agents.ai_random_heuristic_agent import AiRandomHeuristicAgent
from flanker_ai.agents.ai_search_agent import AiSearchAgent
from flanker_ai.config_models import (
    AiConfigComponent,
    HeuristicPolicyConfig,
    SearchPolicyConfig,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState
from flanker_core.systems.action_system import ActionSystem


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: AiSearchAgent | AiRandomHeuristicAgent


class AiSystem:

    @dataclass
    class ActionResult:
        faction: InitiativeState.Faction
        action_runtime_seconds: float
        action: Action
        result: ActionResult
        policy_log: AiSearchAgent.AiSearchLog | None

    @staticmethod
    def perform_action(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> ActionResult | None:
        """
        Performs an action and mutates the state for the given faction.
        This uses the AI config of that faction. Returns `None` if no
        actions are performed.
        """

        if ActionSystem.get_initiative(gs) != faction:
            return None

        start_time = perf_counter()
        config_component: AiConfigComponent | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction == faction:
                config_component = component
                break
        if config_component == None:
            raise ValueError(f"{AiConfigComponent} not found")

        match config_component.config:
            case HeuristicPolicyConfig():
                result = AiRandomHeuristicAgent.perform_action(gs)
                if result is None:
                    return None
                return AiSystem.ActionResult(
                    faction=faction,
                    action_runtime_seconds=perf_counter() - start_time,
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
                    action_runtime_seconds=perf_counter() - start_time,
                    action=result.action,
                    result=result.result,
                    policy_log=result.search_log,
                )

    @staticmethod
    def get_game_tree(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiSearchAgent.GameTreeResult | None:
        """
        Returns a game tree starting from this game node. This uses
        the faction's AI config of this game state. This does not
        mutate the state. Returns `None` if no actions are possible.
        """

        if ActionSystem.get_initiative(gs) != faction:
            return None

        config_component: AiConfigComponent | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction == faction:
                config_component = component
                break
        if config_component == None:
            raise ValueError(f"{AiConfigComponent} not found")

        match config_component.config:
            case SearchPolicyConfig():
                return AiSearchAgent.get_game_tree(
                    gs=gs,
                    config=config_component.config,
                )
            case _:
                raise ValueError("Supprts only search trees.")
