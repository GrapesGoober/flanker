from dataclasses import dataclass

from flanker_ai.actions import ActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class AiMatchTelemetry:
    policy_time: float
    policy_size: int
    policy_branching_factor: int


@dataclass
class AiMatchResult:
    action_results: list[ActionResult]
    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_telemetry: AiMatchTelemetry
    red_telemetry: AiMatchTelemetry


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

        # Let two agents fight each other over and over
        action_results: list[ActionResult] = []
        objective_system = gs.get(ObjectiveSystem)
        while (winner := objective_system.get_winning_faction(gs)) == None:
            blue_action_results = blue_agent.play_initiative()
            red_action_results = red_agent.play_initiative()
            action_results += blue_action_results + red_action_results

            # If both agents have no actions, then consider it draw
            if not red_action_results and not blue_action_results:
                break

        return AiMatchResult(
            action_results=action_results,
            winner=winner,
            total_runtime=0,
            blue_telemetry=AiMatchTelemetry(
                policy_time=0,
                policy_size=0,
                policy_branching_factor=0,
            ),
            red_telemetry=AiMatchTelemetry(
                policy_time=0,
                policy_size=0,
                policy_branching_factor=0,
            ),
        )
