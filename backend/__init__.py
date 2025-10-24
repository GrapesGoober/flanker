from typing import NoReturn
from fastapi import FastAPI, HTTPException, Request, status, Path, Body
from backend.action_service import ActionService
from backend.ai_service import AiService
from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    TerrainModel,
    MoveActionRequest,
    CombatUnitsViewState,
    ActionLog,
)
from backend.combat_unit_service import CombatUnitService
from backend.scene_service import SceneService
from backend.terrain_service import TerrainService
from backend.logging_service import LoggingService

app = FastAPI()
scene_service = SceneService()
id_counter = 0


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> NoReturn:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc)


@app.post("/api/{sceneName}/{gameId}/save/{newScene}")
async def save_game(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
    new_scene: str = Path(..., alias="newScene"),
) -> None:
    """Saves a game into a scene."""
    scene_service.save_scene(scene_name, game_id, f"./scenes/{new_scene}.json")


@app.get("/api/{sceneName}/{gameId}/units")
async def get_units(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
) -> CombatUnitsViewState:
    """Get all combat units for the player faction."""
    gs = scene_service.get_game_state(scene_name, game_id)
    return CombatUnitService.get_units(gs)


@app.get("/api/{sceneName}/{gameId}/terrain")
async def get_terrain(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
) -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    gs = scene_service.get_game_state(scene_name, game_id)
    return TerrainService.get_terrains(gs)


@app.post("/api/{sceneName}/{gameId}/move")
async def action_move(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
    body: MoveActionRequest = Body(...),
) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = scene_service.get_game_state(scene_name, game_id)
    ActionService.move(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/{sceneName}/{gameId}/fire")
async def action_fire(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
    body: FireActionRequest = Body(...),
) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = scene_service.get_game_state(scene_name, game_id)
    ActionService.fire(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/{sceneName}/{gameId}/assault")
async def action_assault(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
    body: AssaultActionRequest = Body(...),
) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = scene_service.get_game_state(scene_name, game_id)
    ActionService.assault(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.get("/api/{sceneName}/{gameId}/logs")
async def get_logs(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
) -> list[ActionLog]:
    gs = scene_service.get_game_state(scene_name, game_id)
    return LoggingService.get_logs(gs)


@app.post("/api/{sceneName}/{gameId}/ai-play")
async def ai_play(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
) -> None:
    gs = scene_service.get_game_state(scene_name, game_id)
    _, logs = AiService.play_minimax(gs, 4)
    for log in logs:
        LoggingService.log(gs, log)


@app.put("/api/{sceneName}/{gameId}/terrain")
async def update_terrain(
    scene_name: str = Path(..., alias="sceneName"),
    game_id: int = Path(..., alias="gameId"),
    body: TerrainModel = Body(...),
) -> None:
    """Edit the terrain polygon."""
    gs = scene_service.get_game_state(scene_name, game_id)
    TerrainService.update_terrain(gs, body)
