from dataclasses import dataclass
import pytest

from core.components import Faction, MoveControls, CombatUnit
from core.gamestate import GameState
from core.los_system import Transform
from core.move_system import MoveSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_id: int
    faction_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Command unit without initiative
    faction_id = gs.add_entity(Faction(has_initiative=False))
    unit_id = gs.add_entity(
        MoveControls(),
        CombatUnit(command_id=faction_id),
        Transform(position=Vec2(0, 0)),
    )
    return Fixture(gs, unit_id, faction_id)


def test_no_initiative(fixture: Fixture) -> None:
    # Try to move the unit
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Should not move from original position
    assert transform.position == Vec2(0, 0), "Unit without initiative musn't move"


def test_has_initiative(fixture: Fixture) -> None:
    # Test with has_initiative=True
    faction = fixture.gs.get_component(fixture.faction_id, Faction)
    assert faction != None
    faction.has_initiative = True
    # Try to move the unit
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(10, 10))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Expects to move to new position
    assert transform.position == Vec2(10, 10), "Unit with initiative can move"
