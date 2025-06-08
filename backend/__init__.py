from fastapi import FastAPI

from backend.scene import create_gamestate
from backend.assets import (
    SquadModel,
    TerrainModel,
    MoveActionRequest,
    get_squads,
    get_terrains,
)
from core.move_action import MoveAction

gs = create_gamestate()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    return get_squads(gs)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> list[SquadModel]:
    MoveAction.move(gs, body.unit_id, body.to)
    return get_squads(gs)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return get_terrains(gs)
