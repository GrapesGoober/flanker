from fastapi import FastAPI
import esper

from backend.scene import create_scene
from core.components import TerrainFeature, Transform, UnitCondition
from backend.domain import SquadModel, TerrainModel

create_scene()
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
