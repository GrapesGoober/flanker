from dataclasses import dataclass
import pytest

from core.components import Faction, MoveControls, CombatUnit
from core.faction_system import FactionSystem
from core.gamestate import GameState
from core.los_system import Transform
from core.move_system import MoveSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(Faction())
    unit_id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=Faction.FactionType.RED),
        Transform(position=Vec2(0, 0)),
    )
    return Fixture(gs, unit_id)


def test_no_initiative(fixture: Fixture) -> None:
    # Test with no initiative
    FactionSystem.set_initiative(fixture.gs, Faction.FactionType.BLUE)
    # Try to move the unit
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Should not move from original position
    assert transform.position == Vec2(0, 0), "Unit without initiative musn't move"


def test_has_initiative(fixture: Fixture) -> None:
    # Try to move the unit
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Expects to move to new position
    assert transform.position == Vec2(10, 10), "Unit with initiative can move"
