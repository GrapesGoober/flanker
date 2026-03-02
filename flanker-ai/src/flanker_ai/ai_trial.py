from dataclasses import dataclass

from flanker_ai.actions import ActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class AiTrialResult:
    action_results: list[ActionResult]
    winner: InitiativeState.Faction | None


class AiTrial:
    """Utility for running game state as a 2-agent trial."""

    @staticmethod
    def run_trial(gs: GameState) -> AiTrialResult:
        blue_agent = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
        red_agent = AiAgent.get_agent(gs, InitiativeState.Faction.RED)
        action_results: list[ActionResult] = []

        # Let two agents fight each other over and over
        while (winner := ObjectiveSystem.get_winning_faction(gs)) == None:
            blue_action_results = blue_agent.play_initiative()
            red_action_results = red_agent.play_initiative()
            action_results += blue_action_results + red_action_results

            # If both agents have no actions, then consider it draw
            if not red_action_results and not blue_action_results:
                break

        return AiTrialResult(
            action_results=action_results,
            winner=winner,
        )
