from fastapi import FastAPI
from backend.action_controller import ActionController
from backend.scene import new_scene
from backend.models import (
    TerrainModel,
    MoveActionRequest,
)
from backend.squad_controller import UnitStateController, UnitState
from backend.terrain_controller import TerrainController

context = new_scene()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> UnitState:
    return UnitStateController.get_unit_state(
        context.gs,
        context.player_faction_id,
    )


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> UnitState:
    return ActionController.move(
        gs=context.gs,
        body=body,
        player_faction_id=context.player_faction_id,
        opponent_faction_id=context.opponent_faction_id,
    )


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return TerrainController.get_terrains(context.gs)
