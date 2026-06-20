from dataclasses import dataclass
from math import inf
from time import perf_counter

from flanker_ai.actions import ActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.objective_system import ObjectiveSystem

MAX_RUNTIME_SECONDS = inf


@dataclass
class AiMatchResult:
    runtime: float
    action_results: list[ActionResult]
    winner: InitiativeState.Faction | None
    blue_search_size: int
    red_search_size: int


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

        blue_search_size: int = 0
        red_search_size: int = 0

        def count_blue_search_size() -> None:
            nonlocal blue_search_size
            blue_search_size += 1

        def count_redsearch_size() -> None:
            nonlocal red_search_size
            red_search_size += 1

        # Let two agents fight each other over and over
        action_results: list[ActionResult] = []
        start_time = perf_counter()
        objective_system = gs.get(ObjectiveSystem)
        while (winner := objective_system.get_winning_faction(gs)) == None:

            # Max safety time limit per run so it doesn't consume CPU.
            runtime = perf_counter() - start_time
            if runtime > MAX_RUNTIME_SECONDS:
                break

            # Have the AI play agianst each other.
            blue_action_results = blue_agent.play_initiative(
                callback=count_blue_search_size,
            )
            red_action_results = red_agent.play_initiative(
                callback=count_redsearch_size,
            )
            action_results += blue_action_results + red_action_results

            # If both agents have no actions, then consider it draw
            if not red_action_results and not blue_action_results:
                break

        runtime = perf_counter() - start_time
        return AiMatchResult(
            runtime=runtime,
            action_results=action_results,
            winner=winner,
            blue_search_size=blue_search_size,
            red_search_size=red_search_size,
        )
