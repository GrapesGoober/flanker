from dataclasses import dataclass

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.fire_system import FireSystem
import math
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass
class Fixture:
    gs: GameState
    attacker_id: int
    target_id: int
    fire_controls: FireControls
    attacker_unit: CombatUnit


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    attacker_id = gs.add_entity(
        attacker_unit := CombatUnit(
            faction=InitiativeState.Faction.BLUE,
        ),
        fire_controls := FireControls(),
        Transform(position=Vec2(7.6, -10)),
    )
    target_id = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.RED,
        ),
        Transform(position=Vec2(15, 20)),
    )
    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
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
        attacker_unit=attacker_unit,
    )

def test_no_los(fixture: Fixture) -> None:
    # Set attacker to position that is obstructed
    attacker_transform = fixture.gs.get_component(
        fixture.attacker_id,
        Transform,
    )
    attacker_transform.position = Vec2(0, -10)
    # Fire action won't occur
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == InvalidAction.BAD_COORDS, "Fire action mustn't occur"

def test_fov_block(fixture: Fixture) -> None:
    # Attack target is behind attacker; LOS clear but FOV blocks
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.position = Vec2(0, 0)
    att.degrees = 0  # facing +x
    tar.position = Vec2(-10, 0)  # behind on -x
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result == InvalidAction.BAD_COORDS, "Fire should be blocked by FOV"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as it is obstructed"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == True
    ), "Expects shooter to retain initiative"

def test_no_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.MISS
    # orient attacker toward target so FOV permits firing
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as fire action MISS"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == False
    ), "Expects attacker to lose initiative"

def test_pin_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.PIN
    # ensure attacker facing target
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.PINNED
    ), "Target expects to be PINNED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == False
    ), "Expects attacker to lose initiative"

def test_suppress_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.SUPPRESS
    # orient attacker toward target
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fixture.gs.get_component(fixture.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be SUPPRESSED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == True
    ), "Expects attacker to retain initiative"

    fixture.fire_controls.override = FireOutcomes.PIN
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    assert (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Expects PIN outcome to not overwrite SUPPRESSED status."
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == False
    ), "Expects attacker to lose initiative"

def test_kill_fire(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.KILL
    # orient attacker toward target
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fixture.gs.try_component(fixture.target_id, CombatUnit)
    assert target == None, "Target expects to be KILLED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.attacker_id) == True
    ), "Expects attacker to retain initiative"

def test_status_pinned(fixture: Fixture) -> None:
    # orient attacker toward target (not used but for consistency)
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fixture.attacker_unit.status = CombatUnit.Status.PINNED
    fixture.fire_controls.override = FireOutcomes.KILL
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert fire_result != None, "PINNED unit can do fire action"

def test_status_supppressed(fixture: Fixture) -> None:
    # orient attacker toward target
    att = fixture.gs.get_component(fixture.attacker_id, Transform)
    tar = fixture.gs.get_component(fixture.target_id, Transform)
    att.degrees = math.degrees(math.atan2(tar.position.y - att.position.y, tar.position.x - att.position.x))
    fixture.attacker_unit.status = CombatUnit.Status.SUPPRESSED
    fixture.fire_controls.override = FireOutcomes.KILL
    fire_result = FireSystem.fire(
        fixture.gs,
        fixture.attacker_id,
        fixture.target_id,
    )
    assert (
        fire_result == InvalidAction.INACTIVE_UNIT
    ), "SUPPRESSED unit can't do fire action"
