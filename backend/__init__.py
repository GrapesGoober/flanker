from fastapi import FastAPI
from backend.action_service import ActionService
from backend.ai_service import AiService
from backend.models import (
    FireActionRequest,
    TerrainModel,
    MoveActionRequest,
    CombatUnitsViewState,
)
from backend.combat_unit_service import CombatUnitService
from backend.scene_service import SceneService
from backend.terrain_service import TerrainService

SCENE_PATH = "./scenes/demo.json"
context = SceneService.load_scene(SCENE_PATH)
app = FastAPI()


@app.get("/api/units")
async def get_units() -> CombatUnitsViewState:
    """Get all combat units for the player faction."""
    return CombatUnitService.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    return TerrainService.get_terrains(context.gs)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionService.move(
        gs=context.gs,
        body=body,
        player_faction_id=context.player_faction_id,
    )
    AiService.play(context.gs, context.opponent_faction_id)
    return CombatUnitService.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.post("/api/fire")
async def action_fire(body: FireActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionService.fire(
        gs=context.gs,
        body=body,
        player_faction_id=context.player_faction_id,
    )
    AiService.play(context.gs, context.opponent_faction_id)
    return CombatUnitService.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.post("/api/reset")
async def reset_scene() -> None:
    """Resets the scene."""
    global context
    context = SceneService.load_scene(SCENE_PATH)


@app.put("/api/terrain")
async def update_terrain(body: TerrainModel) -> None:
    """Edit the terrain polygon."""
    TerrainService.update_terrain(context.gs, body)
    SceneService.save_scene(SCENE_PATH, context.gs)
