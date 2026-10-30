from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    Action,
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
    RallyAction,
    RallyActionResult,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem
from webapi.models.action_models import (
    ActionLogModel,
    ActionModel,
    AssaultActionLogModel,
    AssaultActionModel,
    FireActionLogModel,
    FireActionModel,
    MoveActionLogModel,
    MoveActionModel,
    PivotActionLogModel,
    PivotActionModel,
    RallyActionLogModel,
    RallyActionModel,
)
from webapi.models.state_models import GameViewStateModel
from webapi.services.game_view_service import GameViewService
from webapi.services.logging_service import LoggingService


# TODO: find some ways to clean this up. The core should be able to dispatch.
# This service should handle mapping instead, which is already implemented in
# AiService. That shouldn't do action model mapping.
class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def perform(
        gs: GameState,
        action_model: ActionModel,
    ) -> None:
        """Perform an action."""
        action = ActionService.map_model_to_action(action_model)
        result = ActionSystem.perform(gs, action)
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs=gs,
            log=ActionService.map_action_result_to_logs(
                action=action,
                result=result,
                view_state_snapshot=GameViewService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _move(
        gs: GameState,
        body: MoveActionModel,
    ) -> None:
        result = ActionSystem.perform(
            gs=gs,
            action=MoveAction(
                unit_id=body.unit_id,
                to=body.to,
            ),
        )
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs,
            MoveActionLogModel(
                body=body,
                reactive_fire_outcomes=result.reactive_fire_outcomes,
                view_state=GameViewService.get_view_state(gs),
            ),
        )

    @staticmethod
    def map_action_to_model(
        action: Action,
    ) -> ActionModel:
        match action:
            case MoveAction():
                return MoveActionModel(
                    action_type="MoveActionModel",
                    unit_id=action.unit_id,
                    to=action.to,
                )
            case PivotAction():
                return PivotActionModel(
                    action_type="PivotActionModel",
                    unit_id=action.unit_id,
                    to=action.to,
                )
            case FireAction():
                return FireActionModel(
                    action_type="FireActionModel",
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case AssaultAction():
                return AssaultActionModel(
                    action_type="AssaultActionModel",
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case RallyAction():
                return RallyActionModel(
                    action_type="RallyActionModel",
                    unit_id=action.unit_id,
                )

    @staticmethod
    def map_model_to_action(
        action_model: ActionModel,
    ) -> Action:
        match action_model:
            case MoveActionModel():
                return MoveAction(
                    unit_id=action_model.unit_id,
                    to=action_model.to,
                )
            case PivotActionModel():
                return PivotAction(
                    unit_id=action_model.unit_id,
                    to=action_model.to,
                )
            case FireActionModel():
                return FireAction(
                    unit_id=action_model.unit_id,
                    target_id=action_model.target_id,
                )
            case AssaultActionModel():
                return AssaultAction(
                    unit_id=action_model.unit_id,
                    target_id=action_model.target_id,
                )
            case RallyActionModel():
                return RallyAction(
                    unit_id=action_model.unit_id,
                )

    @staticmethod
    def map_action_result_to_logs(
        action: Action,
        result: ActionResult,
        view_state_snapshot: GameViewStateModel,
    ) -> ActionLogModel:
        match action, result:
            case MoveAction(), MoveActionResult():
                return MoveActionLogModel(
                    body=MoveActionModel(
                        unit_id=action.unit_id,
                        to=action.to,
                    ),
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )

            case PivotAction(), PivotActionResult():
                return PivotActionLogModel(
                    body=PivotActionModel(
                        unit_id=action.unit_id,
                        to=action.to,
                    ),
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )
            case FireAction(), FireActionResult():
                return FireActionLogModel(
                    body=FireActionModel(
                        unit_id=action.unit_id,
                        target_id=action.target_id,
                    ),
                    outcome=result.outcome,
                    view_state=view_state_snapshot,
                )
            case AssaultAction(), AssaultActionResult():
                return AssaultActionLogModel(
                    body=AssaultActionModel(
                        unit_id=action.unit_id,
                        target_id=action.target_id,
                    ),
                    outcome=result.outcome,
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )
            case RallyAction(), RallyActionResult():
                return RallyActionLogModel(
                    body=RallyActionModel(
                        unit_id=action.unit_id,
                    ),
                    outcome=result.outcome,
                    view_state=view_state_snapshot,
                )

            case _:
                raise ValueError(f"Unknown type {result=}")
