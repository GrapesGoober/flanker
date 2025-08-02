from fastapi import FastAPI
from backend.action_controller import ActionController
from backend.models import (
    FireActionRequest,
    TerrainTransformModel,
    TerrainModel,
    MoveActionRequest,
)
from backend.combat_unit_controller import CombatUnitController, CombatUnitsViewState
from backend.scene_manager import SceneManager
from backend.terrain_controller import TerrainController

SCENE_PATH = "./scenes/demo.json"
context = SceneManager.load_scene(SCENE_PATH)
app = FastAPI()


@app.get("/api/units")
async def get_units() -> CombatUnitsViewState:
    """Get all combat units for the player faction."""
    return CombatUnitController.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    """Get all terrain tiles for the current game state."""
    return TerrainController.get_terrains(context.gs)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionController.move(
        gs=context.gs,
        body=body,
        player_faction_id=context.player_faction_id,
        opponent_faction_id=context.opponent_faction_id,
    )
    return CombatUnitController.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.post("/api/fire")
async def action_fire(body: FireActionRequest) -> CombatUnitsViewState:
    """Move a unit and return updated rifle squads."""
    ActionController.fire(
        gs=context.gs,
        body=body,
        player_faction_id=context.player_faction_id,
        opponent_faction_id=context.opponent_faction_id,
    )
    return CombatUnitController.get_units(
        context.gs,
        context.player_faction_id,
    )


@app.post("/api/editor/save")
async def save_scene() -> None:
    """Save the scene."""
    SceneManager.save_scene(SCENE_PATH, context.gs)


@app.get("/api/editor/terrain_transform")
async def get_terrain_transform() -> list[TerrainTransformModel]:
    """Get transformation data for terrain features."""
    return list(TerrainController.get_terrain_transform(context.gs))


@app.put("/api/editor/terrain_transform")
async def update_terrain_transform(body: TerrainTransformModel) -> None:
    """Edit the terrain polygon."""
    TerrainController.transform_terrain(context.gs, body)
