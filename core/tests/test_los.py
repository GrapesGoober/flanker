from dataclasses import dataclass
import pytest

from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.los_system import LosSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    source_id: int
    target_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Two entities
    target = gs.add_entity(Transform(position=Vec2(0, -10)))
    source = gs.add_entity(Transform(position=Vec2(15, 10)))
    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )
    # 5x5 opaque box to the left
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-5, 0),
                Vec2(-10, 0),
                Vec2(-10, 5),
                Vec2(-5, 5),
                Vec2(-5, 0),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )

    return Fixture(gs, source, target)


def test_no_los(fixture: Fixture) -> None:
    has_los = LosSystem.check(fixture.gs, fixture.source_id, fixture.target_id)
    assert has_los == False, "Expects no LOS found"


def test_los(fixture: Fixture) -> None:
    transform = fixture.gs.get_component(fixture.target_id, Transform)
    transform.position = Vec2(6, -10)
    has_los = LosSystem.check(fixture.gs, fixture.source_id, fixture.target_id)
    assert has_los == True, "Expects LOS as target in open view"


def test_los_target_inside_terrain(fixture: Fixture) -> None:
    transform = fixture.gs.get_component(fixture.target_id, Transform)
    transform.position = Vec2(5, 1)
    has_los = LosSystem.check(fixture.gs, fixture.source_id, fixture.target_id)
    assert has_los == True, "Expects LOS as target in terrain"


def test_los_source_inside_terrain(fixture: Fixture) -> None:
    transform = fixture.gs.get_component(fixture.source_id, Transform)
    transform.position = Vec2(9, 9)
    has_los = LosSystem.check(fixture.gs, fixture.source_id, fixture.target_id)
    assert has_los == True, "Expects LOS as source in terrain"


def test_los_both_inside_terrain(fixture: Fixture) -> None:
    source_transform = fixture.gs.get_component(fixture.source_id, Transform)
    source_transform.position = Vec2(9, 9)
    target_transform = fixture.gs.get_component(fixture.target_id, Transform)
    target_transform.position = Vec2(-6, 4)
    has_los = LosSystem.check(fixture.gs, fixture.source_id, fixture.target_id)
    assert has_los == True, "Expects LOS as both are in terrain"
