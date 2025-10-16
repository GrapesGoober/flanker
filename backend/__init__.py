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
from core.gamestate import GameState

app = FastAPI()
games: dict[int, GameState] = {}
id_counter = 0


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> NoReturn:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc)


@app.post("/api/game/load/{save_name}")
async def load_game(save_name: str) -> int:
    """Loads a game from a save."""
    global id_counter
    game_id = id_counter
    id_counter += 1
    games[game_id] = SceneService.load_scene(f"./scenes/{save_name}.json")
    return game_id


@app.post("/api/game/{game_id}/save/{save_name}")
async def save_game(game_id: int, save_name: str) -> None:
    """Saves a game into a scene."""
    SceneService.save_scene(f"./scenes/{save_name}.json", games[game_id])


@app.get("/api/game/{game_id}/units")
async def get_units(game_id: int) -> CombatUnitsViewState:
    """Get all combat units for the player faction."""
    gs = games[game_id]
    return CombatUnitService.get_units(gs)


@app.get("/api/game/{game_id}/terrain")
async def get_terrain(game_id: int) -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    gs = games[game_id]
    return TerrainService.get_terrains(gs)


@app.post("/api/game/{game_id}/move")
async def action_move(game_id: int, body: MoveActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = games[game_id]
    ActionService.move(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/game/{game_id}/fire")
async def action_fire(game_id: int, body: FireActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = games[game_id]
    ActionService.fire(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.post("/api/game/{game_id}/assault")
async def action_assault(
    game_id: int, body: AssaultActionRequest
) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    gs = games[game_id]
    ActionService.assault(gs, body)
    AiService.play(gs)
    return CombatUnitService.get_units(gs)


@app.get("/api/game/{game_id}/logs")
async def get_logs(game_id: int) -> list[ActionLog]:
    gs = games[game_id]
    return LoggingService.get_logs(gs)


@app.post("/api/game/{game_id}/ai-play")
async def ai_play(game_id: int) -> None:
    gs = games[game_id]
    _, logs = AiService.play_minimax(gs, 4)
    for log in logs:
        LoggingService.log(gs, log)


@app.put("/api/edit/{game_id}/terrain")
async def update_terrain(game_id: int, body: TerrainModel) -> None:
    """Edit the terrain polygon."""
    gs = games[game_id]
    TerrainService.update_terrain(gs, body)
