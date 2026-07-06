from dataclasses import dataclass
from time import perf_counter

from flanker_ai.actions import ActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class AiMatchResult:
    runtime: float
    action_results: list[ActionResult]
    winner: InitiativeState.Faction | None
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class AiMatch:
    """Utility for running a match between 2 AI agents."""

    @staticmethod
    def run_match(
        gs: GameState,
    ) -> AiMatchResult:
        """Runs the given game match with 2 AIs and returns results."""

        # Sets up a match
        blue_agent = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
        red_agent = AiAgent.get_agent(gs, InitiativeState.Faction.RED)
        blue_search_sizes: list[int] = []
        red_search_sizes: list[int] = []

        # Let two agents fight each other over and over
        action_results: list[ActionResult] = []
        start_time = perf_counter()
        while (winner := ObjectiveSystem.get_winning_faction(gs)) == None:

            # Have the AI play agianst each other.
            blue_action_results = blue_agent.play_initiative()
            red_action_results = red_agent.play_initiative()
            for action_result, search_size in blue_action_results:
                blue_search_sizes.append(search_size)
                action_results.append(action_result)

            for action_result, search_size in red_action_results:
                red_search_sizes.append(search_size)
                action_results.append(action_result)

            # If both agents have no actions, then consider it draw
            if red_action_results == [] and blue_action_results == []:
                break

        runtime = perf_counter() - start_time
        return AiMatchResult(
            runtime=runtime,
            action_results=action_results,
            winner=winner,
            blue_search_sizes=blue_search_sizes,
            red_search_sizes=red_search_sizes,
        )
