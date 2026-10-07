from uuid import UUID

from fastapi import APIRouter, Body, Query
from webapi.ai_service import AiService
from webapi.combat_unit_service import CombatUnitService
from webapi.models import (
    AiWaypointConfigRequest,
    GameViewStateResponse,
    SquadModel,
    TerrainModel,
)
from webapi.scene_service import SceneService
from webapi.terrain_service import TerrainService

router = APIRouter(prefix="/api/editor")


@router.put("/ai-waypoints")
async def ai_config_waypoints(
    state: str = Body(...),
    config_request: AiWaypointConfigRequest = Body(..., alias="configRequest"),
) -> GameViewStateResponse:
    gs = SceneService.deserialize(state)
    AiService.set_ai_waypoints_coordinates(gs, config_request)
    return SceneService.get_view_state_response(gs)


@router.put("/terrain")
async def update_terrain(
    state: str = Body(...),
    terrain: TerrainModel = Body(...),
) -> GameViewStateResponse:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.update_terrain(gs, terrain)
    return SceneService.get_view_state_response(gs)


@router.post("/terrain")
async def add_terrain(
    state: str = Body(...),
    terrain: TerrainModel = Body(...),
) -> GameViewStateResponse:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.add_terrain(gs, terrain)
    return SceneService.get_view_state_response(gs)


@router.delete("/terrain")
async def delete_terrain(
    state: str = Body(...),
    terrain_id: UUID = Query(..., alias="terrainId"),
) -> GameViewStateResponse:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.delete_terrain(gs, terrain_id)
    return SceneService.get_view_state_response(gs)


@router.post("/unit")
async def add_unit(
    state: str = Body(...),
    unit: SquadModel = Body(...),
) -> GameViewStateResponse:
    """Add a new combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.add_unit(gs, unit)
    return SceneService.get_view_state_response(gs)


@router.delete("/unit")
async def delete_unit(
    state: str = Body(...),
    unit_id: UUID = Query(..., alias="unitId"),
) -> GameViewStateResponse:
    """Deletes a combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.delete_unit(gs, unit_id)
    return SceneService.get_view_state_response(gs)


@router.put("/unit")
async def update_unit(
    state: str = Body(...),
    unit: SquadModel = Body(...),
) -> GameViewStateResponse:
    """Edit the combat unit."""
    gs = SceneService.deserialize(state)
    CombatUnitService.update_unit(gs, unit)
    return SceneService.get_view_state_response(gs)
