from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem

from webapi.logging_service import LoggingService
from webapi.models import (
    ActionRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
    PivotActionLog,
    PivotActionRequest,
)
from webapi.scene_service import SceneService


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def perform(gs: GameState, action_request: ActionRequest) -> None:
        """Perform an action."""

        match action_request:
            case MoveActionRequest():
                ActionService._move(gs, action_request)
            case PivotActionRequest():
                ActionService._pivot(gs, action_request)
            case FireActionRequest():
                ActionService._fire(gs, action_request)
            case AssaultActionRequest():
                ActionService._assault(gs, action_request)

    @staticmethod
    def _move(gs: GameState, body: MoveActionRequest) -> None:
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
            MoveActionLog(
                body=body,
                reactive_fire_outcome=result.reactive_fire_outcome,
                view_state=SceneService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _pivot(gs: GameState, body: PivotActionRequest) -> None:
        result = ActionSystem.perform(
            gs=gs,
            action=PivotAction(
                unit_id=body.unit_id,
                to=body.to,
            ),
        )
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs,
            PivotActionLog(
                body=body,
                reactive_fire_outcome=result.reactive_fire_outcome,
                view_state=SceneService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _fire(gs: GameState, body: FireActionRequest) -> None:
        result = ActionSystem.perform(
            gs=gs,
            action=FireAction(
                unit_id=body.unit_id,
                target_id=body.target_id,
            ),
        )
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs,
            FireActionLog(
                body=body,
                outcome=result.outcome,
                view_state=SceneService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _assault(gs: GameState, body: AssaultActionRequest) -> None:
        result = ActionSystem.perform(
            gs=gs,
            action=AssaultAction(
                unit_id=body.unit_id,
                target_id=body.target_id,
            ),
        )
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs,
            AssaultActionLog(
                body=body,
                outcome=result.outcome,
                reactive_fire_outcome=result.reactive_fire_outcome,
                view_state=SceneService.get_view_state(gs),
            ),
        )
