from fastapi import FastAPI

from backend.basic_ai import BasicAi
from backend.scene import new_scene
from backend.models import (
    SquadModel,
    TerrainModel,
    MoveActionRequest,
)
from backend.squad import SquadController
from backend.terrain import TerrainController
from core.move_action import MoveAction

context = new_scene()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    return SquadController.get_squads(context.gs, context.player_faction_id)


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> list[SquadModel]:
    MoveAction.move(context.gs, body.unit_id, body.to)
    BasicAi.play(context.gs, context.opponent_faction_id)
    return SquadController.get_squads(context.gs, context.player_faction_id)


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    return TerrainController.get_terrains(context.gs)
