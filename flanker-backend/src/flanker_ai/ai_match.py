from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter

from flanker_ai.ai_agent_factory import AiAgentFactory
from flanker_ai.ai_random_heuristic_agent import RandomHeuristicLog
from flanker_ai.i_ai_agent import AiActionResult
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class _AiMatchResult:
    total_runtime_seconds: float
    action_results: list[
        AiActionResult[AiSearchLog] | AiActionResult[RandomHeuristicLog]
    ]
    gs_snapshots: list[GameState]
    winner: InitiativeState.Faction | None


class AiMatch:
    """Utility for running a match between 2 AI agents."""

    @staticmethod
    def run_match(
        gs: GameState,
    ) -> _AiMatchResult:
        """Runs the given game match with 2 AIs and returns results."""

        # Sets up a match
        agents = {
            faction: AiAgentFactory.get_agent(gs, faction)
            for faction in [
                InitiativeState.Faction.BLUE,
                InitiativeState.Faction.RED,
            ]
        }

        action_results: list[
            AiActionResult[AiSearchLog] | AiActionResult[RandomHeuristicLog]
        ] = []
        start_time = perf_counter()
        no_action_count = 0
        gs_snapshots: list[GameState] = []

        # Let two agents fight each other over and over until winner found
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

            action_results.append(action_result)
            gs_snapshots.append(deepcopy(gs))

        runtime = perf_counter() - start_time
        return _AiMatchResult(
            total_runtime_seconds=runtime,
            action_results=action_results,
            gs_snapshots=gs_snapshots,
            winner=winner,
        )
