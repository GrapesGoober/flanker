from dataclasses import dataclass

from flanker_ai.ai_random_heuristic_agent import AiRandomHeuristicAgent
from flanker_ai.ai_search_agent import AiSearchAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import HeuristicPolicyConfig, SearchPolicyConfig
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: AiSearchAgent | AiRandomHeuristicAgent


class AiAgentFactory:
    @staticmethod
    def get_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiSearchAgent | AiRandomHeuristicAgent:
        """Use the config to build an AI agent, or reuse agent if exists."""

        # Get the agent instance component if already exists
        for _, agent_instance in gs.query(_AiAgentInstanceComponent):
            if agent_instance.faction != faction:
                continue
            return agent_instance.agent

        # Agent not exist; use the config to create a new one
        config_component: AiConfigComponent | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction == faction:
                config_component = component
                break
        if config_component == None:
            raise ValueError(f"{AiConfigComponent} not found")

        match config_component.config:
            case HeuristicPolicyConfig():
                agent = AiRandomHeuristicAgent()
            case SearchPolicyConfig():
                agent = AiSearchAgent.get_search_agent(
                    gs, faction=faction, config=config_component.config
                )

        gs.add_entity(
            _AiAgentInstanceComponent(
                faction=faction,
                agent=agent,
            )
        )
        return agent
