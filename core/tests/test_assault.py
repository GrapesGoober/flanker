from dataclasses import dataclass
import pytest

from core.action_models import AssaultAction
from core.components import (
    AssaultControls,
    InitiativeState,
    CombatUnit,
    MoveControls,
    Transform,
)
from core.gamestate import GameState
from core.systems.assault_system import AssaultSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id: int
    assault_controls: AssaultControls


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    attacker_id = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
        ),
        Transform(position=Vec2(1, 1)),
        assault_controls := AssaultControls(),
        MoveControls(),
    )
    target_id = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.RED,
        ),
        Transform(position=Vec2(2, 2)),
        AssaultControls(),
    )
    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id=target_id,
        assault_controls=assault_controls,
    )


def test_assault_fail(fixture: Fixture) -> None:
    fixture.assault_controls.override = AssaultControls.Outcomes.FAIL
    AssaultSystem.assault(
        fixture.gs, AssaultAction(fixture.attacker_id, fixture.target_id)
    )
    attacker = fixture.gs.try_component(fixture.attacker_id, CombatUnit)
    assert attacker == None, "Failed assault must destroy attacker"


def test_assault_success(fixture: Fixture) -> None:
    fixture.assault_controls.override = AssaultControls.Outcomes.SUCCESS
    AssaultSystem.assault(
        fixture.gs, AssaultAction(fixture.attacker_id, fixture.target_id)
    )
    attacker = fixture.gs.try_component(fixture.attacker_id, CombatUnit)
    assert attacker != None, "Successful assault mustn't destroy attacker"
    target = fixture.gs.try_component(fixture.target_id, CombatUnit)
    assert target == None, "Successful assault must destroy target"
