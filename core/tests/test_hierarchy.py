from dataclasses import dataclass
import pytest

from core.command_system import CommandSystem
from core.faction_system import FactionSystem
from core.components import Faction, CombatUnit
from core.gamestate import GameState


@dataclass
class Fixture:
    gs: GameState
    faction_id: int
    faction: Faction
    unit_id_1: int
    unit_id_2: int
    unit_id_3: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    faction_id = gs.add_entity(faction := Faction(has_initiative=True))
    unit_id_1 = gs.add_entity(CombatUnit(command_id=faction_id))
    unit_id_2 = gs.add_entity(CombatUnit(command_id=unit_id_1))
    unit_id_3 = gs.add_entity(CombatUnit(command_id=unit_id_1))

    return Fixture(
        gs=gs,
        faction_id=faction_id,
        faction=faction,
        unit_id_1=unit_id_1,
        unit_id_2=unit_id_2,
        unit_id_3=unit_id_3,
    )


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


def test_chain_command(fixture: Fixture) -> None:
    CommandSystem.kill_unit(fixture.gs, fixture.unit_id_1)
    faction_id = FactionSystem.get_faction_id(fixture.gs, fixture.unit_id_2)
    assert faction_id == fixture.faction_id, "Command must pass down on unit death"
    faction_id = FactionSystem.get_faction_id(fixture.gs, fixture.unit_id_3)
    assert faction_id == fixture.faction_id, "Command must pass down on unit death"
    unit_3 = fixture.gs.get_component(fixture.unit_id_3, CombatUnit)
    assert (
        unit_3.command_id == fixture.unit_id_2
    ), "Remaining subordinate units must be assigned to new commander"
