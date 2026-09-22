from flanker_ai.ai_search_agent import AiSearchAgent
from flanker_ai.i_ai_agent import IAiAgent
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState


class AiAgentFactory:
    @staticmethod
    def get_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> IAiAgent[AiSearchLog]:
        """Use the config to build an AI agent, or reuse agent if exists."""

        # TODO: the factory instead handling AI singleton instance and config
        # querying. Pass down the search config to AiSearchAgent.
        # Perhaps pass it down via constructor?
        agent = AiSearchAgent.get_search_agent(gs, faction=faction)
        return agent
