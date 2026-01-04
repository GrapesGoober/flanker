from dataclasses import dataclass

import pytest

from core.gamestate import GameState
from core.models.components import (
    CombatUnit,
    EliminationObjective,
    FireControls,
    InitiativeState,
)
from core.models.outcomes import FireOutcomes
from core.models.vec2 import Vec2
from core.systems.fire_system import FireSystem
from core.systems.los_system import Transform
from core.systems.objective_system import ObjectiveSystem


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id_1: int
    target_id_2: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(
        InitiativeState(),
        EliminationObjective(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_destroy=2,
            units_destroyed_counter=0,
        ),
    )
    attacker_id = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        FireControls(override=FireOutcomes.KILL),
        Transform(position=Vec2(0, 0)),
    )
    target_id_1 = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(1, 1)),
    )
    target_id_2 = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(2, 2)),
    )

    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id_1=target_id_1,
        target_id_2=target_id_2,
    )


def test_kill_one(fixture: Fixture) -> None:
    FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_1,
    )

    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as objective not met"


def test_kill_two(fixture: Fixture) -> None:
    FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_1,
    )
    FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id_2,
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert (
        winner == InitiativeState.Faction.BLUE
    ), "Expects attacker faction as winner as objective is met"
