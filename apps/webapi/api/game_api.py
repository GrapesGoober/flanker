from fastapi import APIRouter, Body
from webapi.models.action_models import ActionLog, ActionModel
from webapi.models.inspection_models import (
    GameStateInspection,
    GameTreeInspection,
)
from webapi.models.state_models import (
    AiMatchResponseModel,
    GameViewState,
    GameViewStateResponse,
    MapViewState,
)
from webapi.services.action_service import ActionService
from webapi.services.ai_service import AiService
from webapi.services.game_view_service import GameViewService
from webapi.services.logging_service import LoggingService
from webapi.services.scene_service import SceneService
from webapi.services.terrain_service import TerrainService

router = APIRouter(prefix="/api/game")


@router.post("/view")
async def get_view_state(
    state: str = Body(...),
) -> GameViewState:
    """Get all the scene's view state for the player faction."""
    gs = SceneService.deserialize(state)
    return GameViewService.get_view_state(gs)


@router.post("/inspect")
async def get_state_inspection(
    state: str = Body(...),
) -> GameStateInspection:
    """Get the detailed inspection data of the scene."""
    gs = SceneService.deserialize(state)
    return GameViewService.get_inspection(gs)


@router.post("/inspect/game-tree")
async def get_tree_inspection(
    state: str = Body(...),
) -> GameTreeInspection | None:
    """Get the detailed game tree given the state."""
    gs = SceneService.deserialize(state)
    return AiService.get_tree_inspection(gs)


@router.post("/map")
async def get_map(
    state: str = Body(...),
) -> MapViewState:
    """Get map data from a scene."""
    gs = SceneService.deserialize(state)
    return TerrainService.get_map(gs)


@router.post("/perform")
async def perform_action(
    action: ActionModel = Body(...),
    state: str = Body(...),
) -> GameViewStateResponse:
    """Move a unit and return updated rifle squads."""
    gs = SceneService.deserialize(state)
    ActionService.perform(gs, action)
    AiService.play_red_initiative(gs)
    return GameViewService.get_view_state_response(gs)


@router.post("/logs")
async def get_logs(
    state: str = Body(...),
) -> list[ActionLog]:
    gs = SceneService.deserialize(state)
    return LoggingService.get_logs(gs)


@router.post("/ai-play")
async def run_match(
    state: str = Body(...),
) -> AiMatchResponseModel:
    gs = SceneService.deserialize(state)
    return AiService.run_match(gs)
