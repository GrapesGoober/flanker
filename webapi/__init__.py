from timeit import timeit
from typing import NoReturn
from uuid import UUID

from fastapi import Body, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from webapi.action_service import ActionService
from webapi.ai_service import AiService
from webapi.logging_service import LoggingService
from webapi.models import (
    ActionLog,
    AiWaypointConfigRequest,
    AssaultActionRequest,
    FireActionRequest,
    GameViewState,
    GameViewStateResponse,
    MoveActionRequest,
    PivotActionRequest,
    TerrainModel,
)
from webapi.scene_service import SceneService
from webapi.terrain_service import TerrainService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

id_counter = 0


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> NoReturn:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc)


@app.get("/api/json")
async def get_game_state_json(
    scene_names: list[str] = Query(..., alias="sceneNames"),
) -> str:
    "Gets a game state serialized entities table."
    gs = SceneService.load_game_state(scene_names)
    return SceneService.serialize(gs)


@app.post("/api/units")
async def get_units(
    state: str = Body(...),
) -> GameViewState:
    """Get all combat units for the player faction."""
    gs = SceneService.deserialize(state)
    return SceneService.get_view_state(gs)


@app.post("/api/terrain")
async def get_terrain(
    state: str = Body(...),
) -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    gs = SceneService.deserialize(state)
    return TerrainService.get_terrains(gs)


@app.post("/api/move")
async def action_move(
    action: MoveActionRequest = Body(...),
    state: str = Body(...),
) -> GameViewStateResponse:
    """Move a unit and return updated rifle squads."""
    gs = SceneService.deserialize(state)
    ActionService.move(gs, action)
    AiService.play_redfor(gs)
    return SceneService.get_view_state_response(gs)


@app.post("/api/pivot")
async def action_pivot(
    action: PivotActionRequest = Body(...),
    state: str = Body(...),
) -> GameViewStateResponse:
    """Pivot a unit and return updated rifle squads."""
    gs = SceneService.deserialize(state)
    ActionService.pivot(gs, action)
    AiService.play_redfor(gs)
    return SceneService.get_view_state_response(gs)


@app.post("/api/fire")
async def action_fire(
    action: FireActionRequest = Body(...),
    state: str = Body(...),
) -> GameViewStateResponse:
    """Move a unit and return updated rifle squads."""
    gs = SceneService.deserialize(state)
    ActionService.fire(gs, action)
    AiService.play_redfor(gs)
    return SceneService.get_view_state_response(gs)


@app.post("/api/assault")
async def action_assault(
    action: AssaultActionRequest = Body(...),
    state: str = Body(...),
) -> GameViewStateResponse:
    """Move a unit and return updated rifle squads."""
    gs = SceneService.deserialize(state)
    ActionService.assault(gs, action)
    AiService.play_redfor(gs)
    return SceneService.get_view_state_response(gs)


@app.post("/api/logs")
async def get_logs(
    state: str = Body(...),
) -> list[ActionLog]:
    gs = SceneService.deserialize(state)
    return LoggingService.get_logs(gs)


@app.post("/api/ai-play")
async def run_match(
    state: str = Body(...),
) -> None:
    gs = SceneService.deserialize(state)
    exec_time = timeit(lambda: AiService.run_match(gs), number=1)
    print(f"Execution time: {exec_time:.6f} seconds")


@app.post("/api/ai-config-waypoints")
async def ai_config_waypoints(
    state: str = Body(...),
    config_request: AiWaypointConfigRequest = Body(...),
) -> None:
    gs = SceneService.deserialize(state)
    AiService.set_ai_waypoints_coordinates(gs, config_request)


@app.post("/api/terrain/update")
async def update_terrain(
    state: str = Body(...),
    terrain: TerrainModel = Body(...),
) -> None:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.update_terrain(gs, terrain)


@app.post("/api/terrain/add")
async def add_terrain(
    state: str = Body(...),
    body: TerrainModel = Body(...),
) -> None:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.add_terrain(gs, body)


@app.post("/api/terrain/delete")
async def delete_terrain(
    state: str = Body(...),
    terrain_id: UUID = Query(..., alias="terrainId"),
) -> None:
    """Edit the terrain polygon."""
    gs = SceneService.deserialize(state)
    TerrainService.delete_terrain(gs, terrain_id)
