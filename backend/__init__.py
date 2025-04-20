from dataclasses import dataclass
from core.components import (
    MovementControls,
    TerrainFeature,
    Transform,
    UnitCondition,
)
from core.vec2 import Vec2
from core.terrain_types import TerrainType, to_flags
from fastapi import FastAPI
import esper


def setup_game_state() -> None:
    esper.create_entity(
        Transform(position=Vec2(0, -50)), MovementControls(), UnitCondition()
    )
    esper.create_entity(
        Transform(position=Vec2(120, 60)), MovementControls(), UnitCondition()
    )

    esper.create_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            vertices=[  # a 10x10 box
                Vec2(0, 0),
                Vec2(150, 0),
                Vec2(150, 50),
                Vec2(0, 50),
                Vec2(0, 0),
            ],
            flag=to_flags(TerrainType.FOREST),
            terrain_type=TerrainType.FOREST,
        ),
    )


app = FastAPI()


@dataclass
class RifleSquadModel:
    unit_id: int
    position: Vec2
    status: UnitCondition.Status


@dataclass
class TerrainFeatureModel:
    feature_id: int
    position: Vec2
    vertices: list[Vec2]
    terrain_type: TerrainType


@app.get("/api/rifle-squad")
async def get_rifle_squads() -> list[RifleSquadModel]:
    response: list[RifleSquadModel] = []
    for ent, (transform, condition) in esper.get_components(Transform, UnitCondition):
        response.append(
            RifleSquadModel(
                unit_id=ent, position=transform.position, status=condition.status
            )
        )
    return response


@app.get("/api/terrain")
async def get_terrain() -> list[TerrainFeatureModel]:
    response: list[TerrainFeatureModel] = []
    for ent, (transform, feat) in esper.get_components(Transform, TerrainFeature):
        response.append(
            TerrainFeatureModel(
                feature_id=ent,
                position=transform.position,
                vertices=feat.vertices,
                terrain_type=feat.terrain_type,
            )
        )
    return response
