from dataclasses import dataclass

import pytest

from core.gamestate import GameState
from core.models.components import (
    CombatUnit,
    InitiativeState,
    MoveControls,
    TerrainFeature,
    Transform,
)
from core.models.vec2 import Vec2
from core.systems.los_system import LosSystem
from core.systems.move_system import MoveSystem


@dataclass
class Fixture:
    gs: GameState
    source_id: int
    target_id: int
    target_transform: Transform


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(InitiativeState())
    # Two entities
    target = gs.add_entity(
        target_transform := Transform(position=Vec2(0, -10)),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        MoveControls(),
    )
    source = gs.add_entity(
        Transform(position=Vec2(15, 10)),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        MoveControls(),
    )

    flag = TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
            ],
            flag=flag,
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
            ],
            flag=flag,
        ),
    )

    return Fixture(gs, source, target, target_transform)


def test_no_los(fixture: Fixture) -> None:
    has_los = LosSystem.check(
        fixture.gs, fixture.source_id, fixture.target_transform.position
    )
    assert has_los == False, "Expects no LOS found"


def test_los(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.target_id, Vec2(6, -10))
    has_los = LosSystem.check(
        fixture.gs, fixture.source_id, fixture.target_transform.position
    )
    assert has_los == True, "Expects LOS as target in open view"


def test_los_target_inside_terrain(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.target_id, Vec2(5, 1))
    has_los = LosSystem.check(
        fixture.gs, fixture.source_id, fixture.target_transform.position
    )
    assert has_los == True, "Expects LOS as target in terrain"


def test_los_source_inside_terrain(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.source_id, Vec2(9, 9))
    has_los = LosSystem.check(
        fixture.gs, fixture.source_id, fixture.target_transform.position
    )
    assert has_los == True, "Expects LOS as source in terrain"


def test_los_both_inside_terrain(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.source_id, Vec2(9, 9))
    MoveSystem.move(fixture.gs, fixture.target_id, Vec2(-6, 4))
    has_los = LosSystem.check(
        fixture.gs, fixture.source_id, fixture.target_transform.position
    )
    assert has_los == True, "Expects LOS as both are in terrain"
