from dataclasses import dataclass
import pytest

from core.components import CommandUnit, MoveControls, CombatUnit
from core.gamestate import GameState
from core.los_check import Transform
from core.move_action import MoveAction
from core.vec2 import Vec2
from core.components import CommandUnit, MoveControls, CombatUnit


@dataclass
class Fixture:
    gs: GameState
    unit_id: int
    cmd_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Command unit without initiative
    cmd_id = gs.add_entity(CommandUnit(has_initiative=False))
    unit_id = gs.add_entity(
        MoveControls(),
        CombatUnit(command_id=cmd_id),
        Transform(position=Vec2(0, 0)),
    )
    return Fixture(gs, unit_id, cmd_id)


def test_no_initiative(fixture: Fixture) -> None:
    # Try to move the unit
    MoveAction.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Should not move from original position
    assert transform and (
        transform.position == Vec2(0, 0)
    ), "Unit without initiative should not move"


def test_has_initiative(fixture: Fixture) -> None:
    # Test with has_initiative=True
    cmd = fixture.gs.get_component(fixture.cmd_id, CommandUnit)
    assert cmd != None
    cmd.has_initiative = True
    # Try to move the unit
    MoveAction.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Expects to move to new position
    assert transform and (
        transform.position == Vec2(10, 10)
    ), "Unit with initiative can move"
