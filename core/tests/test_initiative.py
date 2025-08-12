from dataclasses import dataclass
import pytest

from core.components import InitiativeState, MoveControls, CombatUnit
from core.events import MoveActionInput
from core.faction_system import InitiativeSystem
from core.gamestate import GameState
from core.los_system import Transform
from core.move_system import MoveSystem
from core.utils.vec2 import Vec2
from test_event import EventRegistry


@dataclass
class Fixture:
    gs: GameState
    unit_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.events = EventRegistry(gs, MoveSystem)

    gs.add_entity(InitiativeState())
    unit_id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(0, 0)),
    )
    return Fixture(gs, unit_id)


def test_no_initiative(fixture: Fixture) -> None:
    # Test with no initiative
    InitiativeSystem.set_initiative(fixture.gs, InitiativeState.Faction.BLUE)
    # Try to move the unit
    fixture.gs.events.emit(MoveActionInput(fixture.unit_id, Vec2(10, 10)))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Should not move from original position
    assert transform.position == Vec2(0, 0), "Unit without initiative musn't move"


def test_has_initiative(fixture: Fixture) -> None:
    # Try to move the unit
    fixture.gs.events.emit(MoveActionInput(fixture.unit_id, Vec2(10, 10)))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    # Expects to move to new position
    assert transform.position == Vec2(10, 10), "Unit with initiative can move"
