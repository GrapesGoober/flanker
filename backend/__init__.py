from fastapi import FastAPI, HTTPException, status

from backend.basic_ai import BasicAi
from backend.scene import new_scene
from backend.models import (
    TerrainModel,
    MoveActionRequest,
)
from backend.squad import UnitStateController, UnitState
from backend.terrain import TerrainController
from core.command import Command
from core.move_action import MoveAction

context = new_scene()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> UnitState:
    return UnitStateController.get_unit_state(context.gs, context.player_faction_id)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> UnitState:
    if Command.get_faction_id(context.gs, body.unit_id) != context.player_faction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit {body.unit_id} is not part of player faction",
        )
    MoveAction.move(context.gs, body.unit_id, body.to)
    BasicAi.play(context.gs, context.opponent_faction_id)
    return UnitStateController.get_unit_state(context.gs, context.player_faction_id)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return TerrainController.get_terrains(context.gs)
