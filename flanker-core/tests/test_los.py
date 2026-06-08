from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    gs: GameState
    spotter_id: UUID
    target_id: UUID
    spotter_transform: Transform
    target_transform: Transform


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    register_systems(gs)
    gs.add_entity(InitiativeState())
    # Two combat units
    target_id = gs.add_entity(
        target_transform := Transform(position=Vec2(0, -10)),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        MoveControls(),
    )
    spotter_id = gs.add_entity(
        spotter_transform := Transform(position=Vec2(15, 10)),
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
    # 40x40 boundary box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(40, 40),
                Vec2(40, -40),
                Vec2(-40, -40),
                Vec2(-40, 40),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    return Fixture(
        gs=gs,
        spotter_id=spotter_id,
        target_id=target_id,
        spotter_transform=spotter_transform,
        target_transform=target_transform,
    )


def test_no_los(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    has_los = los_system.has_los(
        fixture.gs,
        fixture.spotter_transform.position,
        fixture.target_transform.position,
    )
    assert has_los == False, "Expects no LOS found"


def test_los(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    move_system = fixture.gs.get(MoveSystem)
    move_system.move(fixture.gs, fixture.target_id, Vec2(6, -10))
    has_los = los_system.has_los(
        fixture.gs,
        fixture.spotter_transform.position,
        fixture.target_transform.position,
    )
    assert has_los == True, "Expects LOS as target in open view"


def test_los_target_inside_terrain(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    move_system = fixture.gs.get(MoveSystem)
    move_system.move(fixture.gs, fixture.target_id, Vec2(5, 1))
    has_los = los_system.has_los(
        fixture.gs,
        fixture.spotter_transform.position,
        fixture.target_transform.position,
    )
    assert has_los == True, "Expects LOS as target in terrain"


def test_los_source_inside_terrain(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    move_system = fixture.gs.get(MoveSystem)
    move_system.move(fixture.gs, fixture.spotter_id, Vec2(9, 9))
    has_los = los_system.has_los(
        fixture.gs,
        fixture.spotter_transform.position,
        fixture.target_transform.position,
    )
    assert has_los == True, "Expects LOS as source in terrain"


def test_los_both_inside_terrain(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    move_system = fixture.gs.get(MoveSystem)
    move_system.move(fixture.gs, fixture.spotter_id, Vec2(9, 9))
    move_system.move(fixture.gs, fixture.target_id, Vec2(-6, 4))
    has_los = los_system.has_los(
        fixture.gs,
        fixture.spotter_transform.position,
        fixture.target_transform.position,
    )
    assert has_los == True, "Expects LOS as both are in terrain"


def test_los_polygon(fixture: Fixture) -> None:
    los_system = fixture.gs.get(LosSystem)
    spotter_transform = fixture.gs.get_component(fixture.spotter_id, Transform)
    los_polygon = los_system.get_los_polygon(fixture.gs, spotter_transform.position)
    # TODO floating points imprecision would be cleared up by removing jitter
    assert los_polygon == [
        Vec2(40, 40),
        Vec2(-40, 40),
        Vec2(-40, 10.000001),
        Vec2(0, 10),
        Vec2(0, 0),
        Vec2(10, 0),
        Vec2(-9.999998881966011, -40),
        Vec2(40, -40),
        Vec2(40, 40),
    ]
