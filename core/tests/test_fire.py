from dataclasses import dataclass
import pytest

from core.components import CommandUnit, TerrainFeature, CombatUnit, Transform
from core.fire_action import FireAction
from core.gamestate import GameState
from core.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    cmd = gs.add_entity(CommandUnit(has_initiative=True))
    attacker_id = gs.add_entity(
        CombatUnit(command_id=cmd), Transform(position=Vec2(0, -10))
    )
    target_id = gs.add_entity(
        CombatUnit(command_id=cmd), Transform(position=Vec2(15, 20))
    )
    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), angle=0),
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
    )


def test_no_fire(fixture: Fixture) -> None:
    FireAction.fire(fixture.gs, fixture.attacker_id, fixture.target_id)
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target and (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target target expects to be ACTIVE as it is obstructed"


def test_fire(fixture: Fixture) -> None:
    attacker_transform = fixture.gs.get_component(fixture.attacker_id, Transform)
    assert attacker_transform
    attacker_transform.position = Vec2(7.6, -10)
    FireAction.fire(fixture.gs, fixture.attacker_id, fixture.target_id)
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target and (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Target target expects to be SUPPRESSED as it is shot at"
