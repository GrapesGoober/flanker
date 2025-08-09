from dataclasses import dataclass
import pytest

from core.components import (
    EliminationObjective,
    FactionManager,
    FireControls,
    CombatUnit,
)
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.los_system import Transform
from core.objective_system import ObjectiveSystem
from core.utils.vec2 import Vec2


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
        FactionManager(),
        EliminationObjective(
            target_faction=FactionManager.FactionType.FACTION_B,
            winning_faction=FactionManager.FactionType.FACTION_A,
            units_to_destroy=2,
            units_destroyed_counter=0,
        ),
    )
    attacker_id = gs.add_entity(
        CombatUnit(faction=FactionManager.FactionType.FACTION_A),
        FireControls(override=FireControls.Outcomes.KILL),
        Transform(position=Vec2(0, 0)),
    )
    target_id_1 = gs.add_entity(
        CombatUnit(faction=FactionManager.FactionType.FACTION_B),
        Transform(position=Vec2(1, 1)),
    )
    target_id_2 = gs.add_entity(
        CombatUnit(faction=FactionManager.FactionType.FACTION_B),
        Transform(position=Vec2(2, 2)),
    )

    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id_1=target_id_1,
        target_id_2=target_id_2,
    )


def test_kill_one(fixture: Fixture) -> None:
    FireSystem.fire(fixture.gs, fixture.attacker_id, fixture.target_id_1)
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as objective not met"


def test_kill_two(fixture: Fixture) -> None:
    FireSystem.fire(fixture.gs, fixture.attacker_id, fixture.target_id_1)
    FireSystem.fire(fixture.gs, fixture.attacker_id, fixture.target_id_2)
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert (
        winner == FactionManager.FactionType.FACTION_A
    ), "Expects attacker faction as winner as objective is met"
