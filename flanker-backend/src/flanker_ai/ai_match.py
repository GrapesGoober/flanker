from dataclasses import dataclass
from time import perf_counter

from flanker_ai.ai_search_agent import AiSearchAgent
from flanker_ai.i_ai_agent import AiActionResult
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class _AiMatchResult:
    total_runtime_seconds: float
    action_results: list[AiActionResult]
    winner: InitiativeState.Faction | None
    search_logs: list[AiSearchLog]


class AiMatch:
    """Utility for running a match between 2 AI agents."""

    @staticmethod
    def run_match(
        gs: GameState,
    ) -> _AiMatchResult:
        """Runs the given game match with 2 AIs and returns results."""

        # Sets up a match
        agents = {
            faction: AiSearchAgent.get_agent(gs, faction)
            for faction in [
                InitiativeState.Faction.BLUE,
                InitiativeState.Faction.RED,
            ]
        }

        logs: list[AiSearchLog] = []

        # Let two agents fight each other over and over until winner found
        action_results: list[AiActionResult] = []
        start_time = perf_counter()
        no_action_count = 0

        while (winner := ObjectiveSystem.get_winning_faction(gs)) is None:

            # Have the agent play its initiative
            agent = agents[InitiativeSystem.get_initiative(gs)]
            action_result = agent.perform_action(gs)

            # If no legal actions are performed, flip initiative or draw
            if action_result is None:
                # If both agents have no legal actions, consider draw
                no_action_count += 1
                if no_action_count >= 2:
                    break

                InitiativeSystem.flip_initiative(gs)
                continue
            else:  # An action was performed, so reset the counter
                no_action_count = 0

            logs.append(action_result.search_log)
            action_results.append(action_result)

        runtime = perf_counter() - start_time
        return _AiMatchResult(
            total_runtime_seconds=runtime,
            action_results=action_results,
            winner=winner,
            search_logs=logs,
        )
