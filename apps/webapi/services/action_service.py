from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
    RallyAction,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem
from webapi.models.action_models import (
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
        action_request: ActionModel,
    ) -> None:
        """Perform an action."""

        match action_request:
            case MoveActionModel():
                ActionService._move(gs, action_request)
            case PivotActionModel():
                ActionService._pivot(gs, action_request)
            case FireActionModel():
                ActionService._fire(gs, action_request)
            case AssaultActionModel():
                ActionService._assault(gs, action_request)
            case RallyActionModel():
                ActionService._rally(gs, action_request)

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
    def _pivot(
        gs: GameState,
        body: PivotActionModel,
    ) -> None:
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
            PivotActionLogModel(
                body=body,
                reactive_fire_outcomes=result.reactive_fire_outcomes,
                view_state=GameViewService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _fire(
        gs: GameState,
        body: FireActionModel,
    ) -> None:
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
            FireActionLogModel(
                body=body,
                outcome=result.outcome,
                view_state=GameViewService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _assault(
        gs: GameState,
        body: AssaultActionModel,
    ) -> None:
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
            AssaultActionLogModel(
                body=body,
                outcome=result.outcome,
                reactive_fire_outcomes=result.reactive_fire_outcomes,
                view_state=GameViewService.get_view_state(gs),
            ),
        )

    @staticmethod
    def _rally(
        gs: GameState,
        body: RallyActionModel,
    ) -> None:
        result = ActionSystem.perform(
            gs=gs,
            action=RallyAction(
                unit_id=body.unit_id,
            ),
        )
        if isinstance(result, InvalidAction):
            raise ValueError(result)
        LoggingService.log(
            gs,
            RallyActionLogModel(
                body=body,
                outcome=result.outcome,
                view_state=GameViewService.get_view_state(gs),
            ),
        )
