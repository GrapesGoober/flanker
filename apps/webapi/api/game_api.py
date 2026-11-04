from fastapi import APIRouter, Body
from webapi.models.action_models import ActionLogModel, ActionModel
from webapi.models.inspection_models import (
    GameStateInspectionModel,
    GameTreeInspectionModel,
)
from webapi.models.state_models import (
    AiMatchResponseModel,
    AiPerformedActionResultModel,
    GameViewStateModel,
    GameViewStateResponseModel,
    MapViewStateModel,
    TranspositionTestRequest,
    TranspositionTestResult,
)
from webapi.services.action_service import ActionService
from webapi.services.ai_service import AiService
from webapi.services.game_view_service import GameViewService
from webapi.services.logging_service import LoggingService
from webapi.services.scene_service import SceneService
from webapi.services.terrain_service import TerrainService

router = APIRouter(prefix="/api/rpc/game")


@router.post("/get-view")
async def get_view_state(
    state: str = Body(...),
) -> GameViewStateModel:
    """Get all the scene's view state for the player faction."""
    gs = SceneService.deserialize(state)
    return GameViewService.get_view_state(gs)


@router.post("/get-inspection")
async def get_state_inspection(
    state: str = Body(...),
) -> GameStateInspectionModel:
    """Get the detailed inspection data of the scene."""
    gs = SceneService.deserialize(state)
    return GameViewService.get_inspection(gs)


@router.post("/get-game-tree")
async def get_tree_inspection(
    state: str = Body(...),
) -> GameTreeInspectionModel | None:
    """Get the detailed game tree given the state."""
    gs = SceneService.deserialize(state)
    return AiService.get_tree_inspection(gs)


@router.post("/get-map")
async def get_map(
    state: str = Body(...),
) -> MapViewStateModel:
    """Get map data from a scene."""
    gs = SceneService.deserialize(state)
    return TerrainService.get_map(gs)


@router.post("/perform")
async def perform_action(
    action: ActionModel = Body(...),
    state: str = Body(...),
) -> GameViewStateResponseModel:
    """Performs an action and returns the mutated view state."""
    gs = SceneService.deserialize(state)
    ActionService.perform(gs, action)
    AiService.play_red_initiative(gs)
    return GameViewService.get_view_state_response(gs)


@router.post("/ai-perform")
async def ai_perform_action(
    state: str = Body(...),
) -> AiPerformedActionResultModel:
    """Have AI perform an action and returns the mutated view state."""
    gs = SceneService.deserialize(state)
    return AiService.perform_action(gs)


@router.post("/get-transposition-test")
async def get_transposition_test_result(
    body: TranspositionTestRequest = Body(...),
) -> TranspositionTestResult:
    """Have AI perform an action and returns the mutated view state."""
    return AiService.get_transposition_test_result(body=body)


@router.post("/get-logs")
async def get_logs(
    state: str = Body(...),
) -> list[ActionLogModel]:
    gs = SceneService.deserialize(state)
    return LoggingService.get_logs(gs)


@router.post("/get-ai-match")
async def get_match_result(
    state: str = Body(...),
) -> AiMatchResponseModel:
    gs = SceneService.deserialize(state)
    return AiService.run_match(gs)
