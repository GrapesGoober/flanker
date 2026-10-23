from uuid import UUID

from fastapi import APIRouter, Body, Query
from webapi.models.state_models import (
    AiWaypointConfigRequestModel,
    GameViewStateResponseModel,
    SquadModel,
    TerrainModel,
)
from webapi.services.ai_service import AiService
from webapi.services.combat_unit_service import CombatUnitService
from webapi.services.game_view_service import GameViewService
from webapi.services.scene_service import SceneService
from webapi.services.terrain_service import TerrainService

router = APIRouter(prefix="/api/rpc/editor")


@router.post("/update-ai-waypoints")
async def update_ai_waypoints(
    state: str = Body(...),
    config_request: AiWaypointConfigRequestModel = Body(..., alias="configRequest"),
) -> GameViewStateResponseModel:
    gs = SceneService.deserialize(state)
    AiService.set_ai_waypoints_coordinates(gs, config_request)
    return GameViewService.get_view_state_response(gs)


@router.post("/update-terrain")
async def update_terrain(
    state: str = Body(...),
    terrain: TerrainModel = Body(...),
) -> GameViewStateResponseModel:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.update_terrain(gs, terrain)
    return GameViewService.get_view_state_response(gs)


@router.post("/add-terrain")
async def add_terrain(
    state: str = Body(...),
    terrain: TerrainModel = Body(...),
) -> GameViewStateResponseModel:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.add_terrain(gs, terrain)
    return GameViewService.get_view_state_response(gs)


@router.post("/delete-terrain")
async def delete_terrain(
    state: str = Body(...),
    terrain_id: UUID = Query(..., alias="terrainId"),
) -> GameViewStateResponseModel:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.delete_terrain(gs, terrain_id)
    return GameViewService.get_view_state_response(gs)


@router.post("/add-unit")
async def add_unit(
    state: str = Body(...),
    unit: SquadModel = Body(...),
) -> GameViewStateResponseModel:
    """Add a new combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.add_unit(gs, unit)
    return GameViewService.get_view_state_response(gs)


@router.post("/delete-unit")
async def delete_unit(
    state: str = Body(...),
    unit_id: UUID = Query(..., alias="unitId"),
) -> GameViewStateResponseModel:
    """Deletes a combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.delete_unit(gs, unit_id)
    return GameViewService.get_view_state_response(gs)


@router.post("/update-unit")
async def update_unit(
    state: str = Body(...),
    unit: SquadModel = Body(...),
) -> GameViewStateResponseModel:
    """Edit the combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.update_unit(gs, unit)
    return GameViewService.get_view_state_response(gs)
