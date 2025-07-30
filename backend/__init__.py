from fastapi import FastAPI
from backend.action_controller import ActionController
from backend.models import (
    FireActionRequest,
    TerrainModel,
    MoveActionRequest,
)
from backend.combat_unit_controller import CombatUnitController, CombatUnitsViewState
from backend.scene_manager import SceneManager
from backend.terrain_controller import TerrainController

context = SceneManager.load_scene()
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
