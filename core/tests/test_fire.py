from dataclasses import dataclass
import pytest

from core.components import (
    Faction,
    FireControls,
    TerrainFeature,
    CombatUnit,
    Transform,
)
from core.fire_action import FireAction
from core.gamestate import GameState
from core.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id: int
    fire_controls: FireControls


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    faction = gs.add_entity(
        Faction(has_initiative=True),
    )
    attacker_id = gs.add_entity(
        CombatUnit(command_id=faction),
        fire_controls := FireControls(),
        Transform(position=Vec2(7.6, -10)),
    )
    target_id = gs.add_entity(
        CombatUnit(command_id=faction),
        Transform(position=Vec2(15, 20)),
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
        fire_controls=fire_controls,
    )


def test_no_los(fixture: Fixture) -> None:
    # Set attacker to position that is obstructed
    attacker_transform = fixture.gs.get_component(
        fixture.attacker_id,
        Transform,
    )
    assert attacker_transform
    attacker_transform.position = Vec2(0, -10)
    # Fire action won't occur
    fire_result = FireAction.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == False, "Fire action mustn't occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target and (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as it is obstructed"


def test_no_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.MISS
    fire_result = FireAction.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == True, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target and (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as fire action MISS"


def test_suppress_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.SUPPRESS
    fire_result = FireAction.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == True, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target and (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be SUPPRESSED as it is shot"


def test_kill_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.KILL
    fire_result = FireAction.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == True, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert target == None, "Target expects to be KILLED as it is shot"
