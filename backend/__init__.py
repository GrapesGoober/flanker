from fastapi import FastAPI
from backend.scene import create_gamestate
from core.components import TerrainFeature, CombatUnit
from backend.assets import SquadModel, TerrainModel, get_terrain_type

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
