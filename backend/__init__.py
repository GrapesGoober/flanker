from fastapi import FastAPI

from backend.scene import create_gamestate
from backend.models import (
    SquadModel,
    TerrainModel,
    MoveActionRequest,
)
from backend.squad import SquadController
from backend.terrain import TerrainController
from core.move_action import MoveAction

gs = create_gamestate()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    return SquadController.get_squads(gs)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> list[SquadModel]:
    MoveAction.move(gs, body.unit_id, body.to)
    return SquadController.get_squads(gs)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return TerrainController.get_terrains(gs)
