from dataclasses import dataclass
import pytest

from core.components import TerrainFeature, CombatUnit
from core.fire_action import FireAction
from core.gamestate import GameState
from core.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id: int
    attacker: CombatUnit
    target: CombatUnit


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    attacker_id = gs.add_entity(attacker := CombatUnit(position=Vec2(0, -10)))
    target_id = gs.add_entity(target := CombatUnit(position=Vec2(15, 20)))
    # 10x10 opaque box
    gs.add_entity(
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )
    return Fixture(
        gs=gs,
        attacker_id=attacker_id,
        target_id=target_id,
        attacker=attacker,
        target=target,
    )


def test_no_fire(fixture: Fixture) -> None:
    FireAction.fire(fixture.gs, fixture.attacker_id, fixture.target_id)
    assert (
        fixture.target.status == CombatUnit.Status.ACTIVE
    ), "Target target expects to be ACTIVE as it is not shot at"


def test_fire(fixture: Fixture) -> None:
    fixture.attacker.position = Vec2(7.6, -10)
    FireAction.fire(fixture.gs, fixture.attacker_id, fixture.target_id)
    assert (
        fixture.target.status == CombatUnit.Status.SUPPRESSED
    ), "Target target expects to be SUPPRESSED as it is shot at"
