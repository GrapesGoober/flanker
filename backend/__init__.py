from fastapi import FastAPI

from backend.scene import new_scene
from backend.models import (
    SquadModel,
    TerrainModel,
    MoveActionRequest,
)
from backend.squad import SquadController
from backend.terrain import TerrainController
from core.move_action import MoveAction

ctx = new_scene()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    return SquadController.get_squads(ctx.gs, ctx.player_command_id)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> list[SquadModel]:
    MoveAction.move(ctx.gs, body.unit_id, body.to)
    return SquadController.get_squads(ctx.gs, ctx.player_command_id)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return TerrainController.get_terrains(ctx.gs)
