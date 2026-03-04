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


# pylint: disable=redefined-outer-name

def test_no_los(fixture: Fixture) -> None:
    # Set attacker to position that is obstructed
    attacker_transform = fx.gs.get_component(
        fx.attacker_id,
        Transform,
    )
    attacker_transform.position = Vec2(0, -10)
    # Fire action won't occur
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result == InvalidAction.BAD_COORDS, "Fire action mustn't occur"


# pylint: disable=redefined-outer-name

def test_fov_block(fixture: Fixture) -> None:
    # Attack target is behind attacker; LOS clear but FOV blocks
    att = fx.gs.get_component(fx.attacker_id, Transform)
    tar = fx.gs.get_component(fx.target_id, Transform)
    att.position = Vec2(0, 0)
    att.degrees = 0  # facing +x
    tar.position = Vec2(-10, 0)  # behind on -x
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result == InvalidAction.BAD_COORDS, "Fire should be blocked by FOV"
    target = fx.gs.get_component(fx.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as it is obstructed"
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == True
    ), "Expects shooter to retain initiative"


# pylint: disable=redefined-outer-name

def test_no_fire(fixture: Fixture) -> None:
    fx.fire_controls.override = FireOutcomes.MISS
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fx.gs.get_component(fx.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.ACTIVE
    ), "Target expects to be ACTIVE as fire action MISS"
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == False
    ), "Expects attacker to lose initiative"


# pylint: disable=redefined-outer-name

def test_pin_fire(fixture: Fixture) -> None:
    fx.fire_controls.override = FireOutcomes.PIN
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fx.gs.get_component(fx.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.PINNED
    ), "Target expects to be PINNED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == False
    ), "Expects attacker to lose initiative"


# pylint: disable=redefined-outer-name

def test_suppress_fire(fixture: Fixture) -> None:
    fx.fire_controls.override = FireOutcomes.SUPPRESS
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fx.gs.get_component(fx.target_id, CombatUnit)
    assert (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be SUPPRESSED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == True
    ), "Expects attacker to retain initiative"

    fx.fire_controls.override = FireOutcomes.PIN
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    assert (
        target.status == CombatUnit.Status.SUPPRESSED
    ), "Expects PIN outcome to not overwrite SUPPRESSED status."
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == False
    ), "Expects attacker to lose initiative"


# pylint: disable=redefined-outer-name

def test_kill_fire(fixture: Fixture) -> None:
    fx.fire_controls.override = FireOutcomes.KILL
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "Fire action must occur"
    target = fx.gs.try_component(fx.target_id, CombatUnit)
    assert target == None, "Target expects to be KILLED as it is shot"
    assert (
        InitiativeSystem.has_initiative(fx.gs, fx.attacker_id) == True
    ), "Expects attacker to retain initiative"


# pylint: disable=redefined-outer-name

def test_status_pinned(fixture: Fixture) -> None:
    fx.attacker_unit.status = CombatUnit.Status.PINNED
    fx.fire_controls.override = FireOutcomes.KILL
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert fire_result != None, "PINNED unit can do fire action"


# pylint: disable=redefined-outer-name

def test_status_supppressed(fixture: Fixture) -> None:
    fx.attacker_unit.status = CombatUnit.Status.SUPPRESSED
    fx.fire_controls.override = FireOutcomes.KILL
    fire_result = FireSystem.fire(
        fx.gs,
        fx.attacker_id,
        fx.target_id,
    )
    assert (
        fire_result == InvalidAction.INACTIVE_UNIT
    ), "SUPPRESSED unit can't do fire action"
