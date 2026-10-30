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
        action_model = ActionService.map_action_to_model(action)
        match action_model, result:
            case MoveActionModel(), MoveActionResult():
                return MoveActionLogModel(
                    body=action_model,
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )
            case PivotActionModel(), PivotActionResult():
                return PivotActionLogModel(
                    body=action_model,
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )
            case FireActionModel(), FireActionResult():
                return FireActionLogModel(
                    body=action_model,
                    outcome=result.outcome,
                    view_state=view_state_snapshot,
                )
            case AssaultActionModel(), AssaultActionResult():
                return AssaultActionLogModel(
                    body=action_model,
                    outcome=result.outcome,
                    reactive_fire_outcomes=result.reactive_fire_outcomes,
                    view_state=view_state_snapshot,
                )
            case RallyActionModel(), RallyActionResult():
                return RallyActionLogModel(
                    body=action_model,
                    outcome=result.outcome,
                    view_state=view_state_snapshot,
                )
            case _:
                raise RuntimeError(
                    f"Action and result pair ({action=}, {result=}) mismatched!"
                )
