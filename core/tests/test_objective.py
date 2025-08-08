from dataclasses import dataclass
import pytest

from core.components import (
    EliminationObjective,
    Faction,
    FireControls,
    CombatUnit,
)
from core.gamestate import GameState
from core.los_system import Transform
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
    target_faction_id = gs.add_entity(
        Faction(has_initiative=False),
    )
    attacker_faction_id = gs.add_entity(
        Faction(has_initiative=True),
        EliminationObjective(
            target_faction_id=target_faction_id,
            units_to_destroy=2,
            units_destroyed_counter=0,
        ),
    )
    attacker_id = gs.add_entity(
        CombatUnit(command_id=attacker_faction_id),
        FireControls(override=FireControls.Outcomes.KILL),
        Transform(position=Vec2(0, 0)),
    )
    target_id_1 = gs.add_entity(
        CombatUnit(command_id=target_faction_id),
        Transform(position=Vec2(1, 1)),
    )
    target_id_2 = gs.add_entity(
        CombatUnit(command_id=target_faction_id),
        Transform(position=Vec2(2, 2)),
    )

    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id_1=target_id_1,
        target_id_2=target_id_2,
    )
