from flanker_ai.ai_agent import (
    AiActionResult,
    AiAgent,
)
from flanker_ai.ai_match import AiMatch
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import (
    PointsConfig,
    SearchPolicyConfig,
    WaypointsStateConfig,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
)
from flanker_core.models.components import InitiativeState

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AiWaypointConfigRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
    PivotActionLog,
    PivotActionRequest,
)


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""
        agent = AiAgent.get_agent(gs, InitiativeState.Faction.RED)
        results = agent.play_initiative()
        action_results = [action_result for action_result in results]
        AiService._log_ai_action_results(gs, action_results)

    @staticmethod
    def run_match(gs: GameState) -> None:
        """Runs a match where 2 AI agents plays against each other."""
        result = AiMatch.run_match(gs)
        AiService._log_ai_action_results(gs, result.action_results)
        if result.winner == None:
            print(f"No winner; draw")
        else:
            print(f"Winner is {result.winner}")

    @staticmethod
    def set_ai_waypoints_coordinates(
        gs: GameState,
        request: AiWaypointConfigRequest,
    ) -> None:
        for _, config_component in gs.query(AiConfigComponent):
            if config_component.faction != request.faction:
                continue
            if not isinstance(config_component.config, SearchPolicyConfig):
                continue
            if not isinstance(config_component.config.state, WaypointsStateConfig):
                continue
            points_config = config_component.config.state.waypoints
            if not isinstance(points_config, PointsConfig.HandDrawnConfig):
                continue
            points_config.points = request.points

    @staticmethod
    def _log_ai_action_results(
        gs: GameState,
        results: list[AiActionResult],
    ) -> None:
        for result in results:
            match result.action, result.result:
                case MoveAction(), MoveActionResult():
                    log = MoveActionLog(
                        body=MoveActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcome=result.result.reactive_fire_outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )

                case PivotAction(), PivotActionResult():
                    log = PivotActionLog(
                        body=PivotActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcome=result.result.reactive_fire_outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case FireAction(), FireActionResult():
                    log = FireActionLog(
                        body=FireActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case AssaultAction(), AssaultActionResult():
                    log = AssaultActionLog(
                        body=AssaultActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )

                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)
