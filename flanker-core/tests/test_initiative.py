from dataclasses import dataclass

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    MoveControls,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


@dataclass
class Fixture:
    gs: GameState
    unit_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(InitiativeState())
    unit_id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, 0)),
    )
    return Fixture(gs, unit_id)


def test_no_initiative(fixture: Fixture) -> None:
    # Test with no initiative
    InitiativeSystem.set_initiative(fixture.gs, InitiativeState.Faction.RED)
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
