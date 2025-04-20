from dataclasses import dataclass
from core.components import (
    MovementControls,
    TerrainFeature,
    Transform,
    UnitCondition,
)
from core.vec2 import Vec2
from core.terrain_types import TerrainType
from fastapi import FastAPI
import esper


def add_rifle_squad(pos: Vec2) -> None:
    esper.create_entity(Transform(position=pos), MovementControls(), UnitCondition())


def add_terrain() -> None:
    esper.create_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            points=[  # a 10x10 box
                Vec2(0, 0),
                Vec2(150, 0),
                Vec2(150, 50),
                Vec2(0, 50),
                Vec2(0, 0),
            ],
            terrain_type=TerrainType.FOREST,
        ),
    )


add_rifle_squad(Vec2(0, -50))
add_rifle_squad(Vec2(120, 60))
add_terrain()

app = FastAPI()


@dataclass
class RifleSquadModel:
    unit_id: int
    position: Vec2
    status: UnitCondition.Status


@dataclass
class TerrainFeatureModel:
    feature_id: int
    terrain_type: TerrainType
    position: Vec2
    vertices: list[Vec2]


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
                terrain_type=feat.terrain_type,
                position=transform.position,
                vertices=feat.points,
            )
        )
    return response
