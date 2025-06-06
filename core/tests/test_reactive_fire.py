from dataclasses import dataclass
import pytest

from core.components import CommandUnit, MoveControls, TerrainFeature, CombatUnit
from core.gamestate import GameState
from core.los_check import Transform
from core.move_action import MoveAction
from core.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    cmd = gs.add_entity(CommandUnit())
    gs.add_entity(
        MoveControls(), CombatUnit(command_id=cmd), Transform(position=Vec2(15, 20))
    )
    id = gs.add_entity(
        MoveControls(), CombatUnit(command_id=cmd), Transform(position=Vec2(0, -10))
    )
    # 10x10 opaque box
    gs.add_entity(
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

    return Fixture(gs, id)


def test_move(fixture: Fixture) -> None:
    MoveAction.move(fixture.gs, fixture.unit_id, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    assert transform and (
        transform.position == Vec2(5, -15)
    ), "Target expects at Vec2(5, -15)"


def test_los_interrupt(fixture: Fixture) -> None:
    MoveAction.move(fixture.gs, fixture.unit_id, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    assert transform and (
        transform.position == Vec2(7.6, -10)
    ), "Target expects at Vec2(7.6, -10)"
    unit = fixture.gs.get_component(fixture.unit_id, CombatUnit)
    assert unit and (
        unit.status == CombatUnit.status.SUPPRESSED
    ), "Target expects to be suppressed"
