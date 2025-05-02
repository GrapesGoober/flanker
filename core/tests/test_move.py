from dataclasses import dataclass
import pytest

from core.components import MovementControls, TerrainFeature, Transform, UnitCondition
from core.ecs import World
from core.move_action import MoveAction
from core.vec2 import Vec2


@dataclass
class Fixture:
    world: World
    unit_id: int
    unit_cond: UnitCondition
    unit_pos: Transform


@pytest.fixture
def fixture() -> Fixture:
    world = World()
    # Rifle Squads
    world.add_entity(
        Transform(position=Vec2(15, 20)), MovementControls(), UnitCondition()
    )
    id = world.add_entity(
        pos := Transform(position=Vec2(0, -10)),
        MovementControls(),
        cond := UnitCondition(),
    )
    # 10x10 opaque box
    world.add_entity(
        Transform(position=Vec2(0, 0)),
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

    return Fixture(world, id, cond, pos)


def test_move(fixture: Fixture) -> None:
    MoveAction.move(fixture.world, fixture.unit_id, Vec2(5, -15))
    assert fixture.unit_pos.position == Vec2(5, -15), "Target expects at Vec2(5, -15)"


def test_los_interrupt(fixture: Fixture) -> None:
    MoveAction.move(fixture.world, fixture.unit_id, Vec2(20, -10))
    assert fixture.unit_pos.position == Vec2(
        7.6, -10
    ), "Target expects at Vec2(7.6, -10)"
    assert (
        fixture.unit_cond.status == UnitCondition.status.SUPPRESSED
    ), "Target expects to be suppressed"
