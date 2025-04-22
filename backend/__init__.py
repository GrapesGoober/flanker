from fastapi import FastAPI
import esper

from core.vec2 import Vec2
from core.components import TerrainFeature, Transform, UnitCondition
from backend.domain import SquadModel, TerrainModel, add_forest, add_squad

add_squad(Vec2(0, -50))
add_squad(Vec2(120, 60))
add_forest(  # a 10x10 box
    [
        Vec2(0, 0),
        Vec2(150, 0),
        Vec2(150, 50),
        Vec2(0, 50),
        Vec2(0, 0),
    ]
)
app = FastAPI()


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[SquadModel]:
    response: list[SquadModel] = []
    for ent, (transform, condition) in esper.get_components(Transform, UnitCondition):
        response.append(
            SquadModel(
                unit_id=ent, position=transform.position, status=condition.status
            )
        )
    return response


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainModel]:
    response: list[TerrainModel] = []
    for ent, (transform, feat) in esper.get_components(Transform, TerrainFeature):
        response.append(
            TerrainModel(
                feature_id=ent,
                position=transform.position,
                vertices=feat.vertices,
                terrain_type=TerrainModel.Types.FOREST,
            )
        )
    return response
