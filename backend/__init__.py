from fastapi import FastAPI

from backend.scene import create_gamestate
from backend.assets import SquadModel, TerrainModel, MoveActionRequest, get_terrain_type
from core.components import TerrainFeature, CombatUnit
from core.move_action import MoveAction

gs = create_gamestate()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    response: list[SquadModel] = []
    for ent, unit in gs.query(CombatUnit):
        response.append(
            SquadModel(unit_id=ent, position=unit.position, status=unit.status)
        )
    return response


@app.post("/api/move")
async def action_move(body: MoveActionRequest) -> list[SquadModel]:
    MoveAction.move(gs, body.unit_id, body.to)
    return await get_rifle_squads()


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    response: list[TerrainModel] = []
    for ent, feat in gs.query(TerrainFeature):
        response.append(
            TerrainModel(
                feature_id=ent,
                vertices=feat.vertices,
                terrain_type=get_terrain_type(feat.flag),
            )
        )
    return response
