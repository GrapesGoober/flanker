from fastapi import APIRouter, Body
from webapi.action_service import ActionService
from webapi.ai_service import AiService
from webapi.game_view_service import GameViewService
from webapi.logging_service import LoggingService
from webapi.models import (
    ActionLog,
    ActionRequest,
    AiMatchResponse,
    GameStateInspection,
    GameViewState,
    GameViewStateResponse,
    MapViewState,
)
from webapi.scene_service import SceneService
from webapi.terrain_service import TerrainService

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


@router.post("/map")
async def get_map(
    state: str = Body(...),
) -> MapViewState:
    """Get map data from a scene."""
    gs = SceneService.deserialize(state)
    return TerrainService.get_map(gs)


@router.post("/perform")
async def perform_action(
    action: ActionRequest = Body(...),
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
) -> AiMatchResponse:
    gs = SceneService.deserialize(state)
    return AiService.run_match(gs)
