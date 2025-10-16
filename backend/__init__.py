from typing import NoReturn
from fastapi import FastAPI, HTTPException, Request, status
from backend.action_service import ActionService
from backend.ai_service import AiService
from backend.log_models import ActionLog
from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    TerrainModel,
    MoveActionRequest,
    CombatUnitsViewState,
)
from backend.combat_unit_service import CombatUnitService
from backend.scene_service import SceneService
from backend.terrain_service import TerrainService
from backend.logging_service import LoggingService

SCENE_PATH = "./scenes/demo.json"
gs = SceneService.load_scene(SCENE_PATH)
app = FastAPI()


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> NoReturn:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc)


@app.get("/api/units")
async def get_units() -> CombatUnitsViewState:
    """Get all combat units for the player faction."""
    return CombatUnitService.get_units(gs)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    return TerrainService.get_terrains(gs)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionService.move(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/fire")
async def action_fire(body: FireActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionService.fire(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/assault")
async def action_assault(body: AssaultActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionService.assault(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/reset")
async def reset_scene() -> None:
    """Resets the scene."""
    global gs
    gs = SceneService.load_scene(SCENE_PATH)


@app.put("/api/terrain")
async def update_terrain(body: TerrainModel) -> None:
    """Edit the terrain polygon."""
    TerrainService.update_terrain(gs, body)
    SceneService.save_scene(SCENE_PATH, gs)


@app.get("/api/logs")
async def get_logs() -> list[ActionLog]:
    return LoggingService.get_logs(gs)


@app.post("/api/ai-play")
async def ai_play() -> None:
    _, logs = AiService.play_minimax(gs, 4)
    for log in logs:
        LoggingService.log(gs, log)
