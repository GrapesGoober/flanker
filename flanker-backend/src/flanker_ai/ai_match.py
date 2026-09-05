from dataclasses import dataclass
from time import perf_counter

from flanker_ai.ai_agent import AiActionResult, AiAgent
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
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
        agents = [
            AiAgent.get_agent(gs, faction)
            for faction in [InitiativeState.Faction.BLUE, InitiativeState.Faction.RED]
        ]

        logs: list[AiSearchLog] = []

        # Let two agents fight each other over and over
        action_results: list[AiActionResult] = []
        start_time = perf_counter()
        while (winner := ObjectiveSystem.get_winning_faction(gs)) == None:

            # Have the AI play agianst each other.
            has_any_action_played: bool = False
            for agent in agents:
                for action_result in agent.play_initiative():
                    has_any_action_played = True
                    logs.append(action_result.search_log)
                    action_results.append(action_result)

            # If both agents have no actions, then consider it draw
            if has_any_action_played == False:
                break

        runtime = perf_counter() - start_time
        return _AiMatchResult(
            total_runtime_seconds=runtime,
            action_results=action_results,
            winner=winner,
            search_logs=logs,
        )
