from dataclasses import dataclass

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass
class Fixture:
    gs: GameState
    initiative: InitiativeState
    unit_root: int
    unit_id_1: int
    unit_id_2: int
    unit_id_3: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(
        initiative := InitiativeState(),
    )
    unit_root = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    unit_id_1 = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            command_id=unit_root,
        )
    )
    unit_id_2 = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            command_id=unit_id_1,
        )
    )
    unit_id_3 = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            command_id=unit_id_1,
        )
    )

    return Fixture(
        gs=gs,
        initiative=initiative,
        unit_root=unit_root,
        unit_id_1=unit_id_1,
        unit_id_2=unit_id_2,
        unit_id_3=unit_id_3,
    )


def test_initiative(fixture: Fixture) -> None:
    has_initiative = InitiativeSystem.has_initiative(fixture.gs, fixture.unit_id_1)
    assert has_initiative == True, "Expects faction BLUE to have initiative"

    has_initiative = InitiativeSystem.has_initiative(fixture.gs, fixture.unit_id_2)
    assert has_initiative == True, "Expects faction BLUE to have initiative"


def test_no_initiative(fixture: Fixture) -> None:
    fixture.initiative.faction = InitiativeState.Faction.RED

    has_initiative = InitiativeSystem.has_initiative(fixture.gs, fixture.unit_id_1)
    assert has_initiative == False, "Expects faction BLUE to no longer have initiative"

    has_initiative = InitiativeSystem.has_initiative(fixture.gs, fixture.unit_id_2)
    assert has_initiative == False, "Expects faction BLUE to no longer have initiative"


def test_chain_command(fixture: Fixture) -> None:
    CommandSystem.kill_unit(fixture.gs, fixture.unit_id_1)
    unit_2 = fixture.gs.get_component(fixture.unit_id_2, CombatUnit)
    assert (
        unit_2.command_id == fixture.unit_root
    ), "Command must pass down on unit death"
    unit_3 = fixture.gs.get_component(fixture.unit_id_3, CombatUnit)
    assert (
        unit_3.command_id == fixture.unit_id_2
    ), "Remaining subordinate units must be assigned to new commander"
