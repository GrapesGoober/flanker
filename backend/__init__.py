from fastapi import FastAPI
from backend.scene import create_world
from core.components import TerrainFeature, CombatUnit
from backend.assets import SquadModel, TerrainModel, get_terrain_type

world = create_world()
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    response: list[SquadModel] = []
    for ent, state in world.get_entities(CombatUnit):
        response.append(
            SquadModel(unit_id=ent, position=state.position, status=state.status)
        )
    return response


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    response: list[TerrainModel] = []
    for ent, feat in world.get_entities(TerrainFeature):
        response.append(
            TerrainModel(
                feature_id=ent,
                vertices=feat.vertices,
                terrain_type=get_terrain_type(feat.flag),
            )
        )
    return response
