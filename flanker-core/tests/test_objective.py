from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    gs: GameState
    attacker_id: UUID
    target_id_1: UUID
    target_id_2: UUID


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    register_systems(gs)
    # Rifle Squads
    gs.add_entity(
        InitiativeState(),
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        ),
    )
    attacker_id = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        FireControls(override=FireOutcomes.KILL),
        Transform(position=Vec2(0, 0)),
    )
    target_id_1 = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(2, 1)),
    )
    target_id_2 = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(3, 1)),
    )

    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id_1=target_id_1,
        target_id_2=target_id_2,
    )


def test_kill_one(fixture: Fixture) -> None:
    fire_system = fixture.gs.get(FireSystem)
    fire_system.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_1,
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as objective not met"


def test_kill_two(fixture: Fixture) -> None:
    fire_system = fixture.gs.get(FireSystem)
    fire_system.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_1,
    )
    fire_system.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_2,
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert (
        winner == InitiativeState.Faction.BLUE
    ), "Expects attacker faction as winner as objective is met"
