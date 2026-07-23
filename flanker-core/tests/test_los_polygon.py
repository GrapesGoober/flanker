from dataclasses import dataclass

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


@dataclass
class Fixture:
    gs: GameState


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()

    # Two intersecting terrains.
    flag = TerrainFeature.Flag.OPAQUE
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(5, 5),
                Vec2(0, 10),
                Vec2(-5, 5),
                Vec2(0, 0),
            ],
            flag=flag,
        ),
    )
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(10, 5),
                Vec2(5, 10),
                Vec2(0, 5),
                Vec2(5, 0),
            ],
            flag=flag,
        ),
    )
    # 2000x2000 boundary
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-1000, -1000),
                Vec2(1000, -1000),
                Vec2(1000, 1000),
                Vec2(-1000, 1000),
                Vec2(-1000, -1000),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    return Fixture(
        gs=gs,
    )


def test_los_polygon(fixture: Fixture) -> None:
    polygon = LosSystem.get_los_polygon(fixture.gs, Vec2(2.5, -2.5))
    assert Vec2(2.5, 2.5) in polygon
