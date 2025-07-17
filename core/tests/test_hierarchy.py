from dataclasses import dataclass
import pytest

from core.faction_system import FactionSystem
from core.components import Faction, CombatUnit
from core.gamestate import GameState


@dataclass
class Fixture:
    gs: GameState
    faction: Faction
    unit_id_1: int
    unit_id_2: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    faction_id = gs.add_entity(faction := Faction(has_initiative=True))
    unit_id_1 = gs.add_entity(CombatUnit(command_id=faction_id))
    unit_id_2 = gs.add_entity(CombatUnit(command_id=unit_id_1))

    return Fixture(gs, faction, unit_id_1, unit_id_2)


def test_initiative(fixture: Fixture) -> None:
    has_initiative = FactionSystem.has_initiative(fixture.gs, fixture.unit_id_1)
    assert has_initiative == True, "Parent Faction entity has initiative"

    has_initiative = FactionSystem.has_initiative(fixture.gs, fixture.unit_id_2)
    assert has_initiative == True, "Parent Faction entity has initiative"


def test_no_initiative(fixture: Fixture) -> None:
    fixture.faction.has_initiative = False

    has_initiative = FactionSystem.has_initiative(fixture.gs, fixture.unit_id_1)
    assert has_initiative == False, "Parent Faction entity has no initiative"

    has_initiative = FactionSystem.has_initiative(fixture.gs, fixture.unit_id_2)
    assert has_initiative == False, "Parent Faction entity has no initiative"
