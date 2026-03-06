from dataclasses import dataclass

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


@dataclass
class Fixture:
    gs: GameState
    unit_move: int
    unit_shoot_1: int
    unit_shoot_2: int
    fire_controls_1: FireControls
    fire_controls_2: FireControls


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    unit_move = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
    )
    # Have the shooters stand on top of each other,
    # so the reactive fire position is the same
    unit_shoot_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        fire_controls_1 := FireControls(),
        Transform(position=Vec2(15, 20)),
    )
    unit_shoot_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        fire_controls_2 := FireControls(),
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
    # 2000x2000 boundary
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-1000, -1000),
                Vec2(1000, -1000),
                Vec2(1000, 1000),
                Vec2(-1000, 1000),
                Vec2(-1000, -1000),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    return Fixture(
        gs=gs,
        unit_move=unit_move,
        unit_shoot_1=unit_shoot_1,
        fire_controls_1=fire_controls_1,
        unit_shoot_2=unit_shoot_2,
        fire_controls_2=fire_controls_2,
    )


def test_no_interrupt(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        5, -15
    ), "Move action expects to not be interrupted"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot_1) == False
    ), "NO reactive fire mustn't flip initiative."


def test_both_miss(fixture: Fixture) -> None:
    fixture.fire_controls_1.override = FireOutcomes.MISS
    fixture.fire_controls_2.override = FireOutcomes.MISS
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        20, -10
    ), "Move action expects to not be interrupted"
    fire_controls = fixture.gs.get_component(fixture.unit_shoot_1, FireControls)
    assert (
        fire_controls.can_reactive_fire == False
    ), "MISS reactive fire results in NO FIRE"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot_1) == False
    ), "MISS reactive fire mustn't flip initiative"
    InitiativeSystem.flip_initiative(fixture.gs)
    assert (
        fire_controls and fire_controls.can_reactive_fire == True
    ), "Passing initiative must reset reactive fire"


def test_one_pin(fixture: Fixture) -> None:
    fixture.fire_controls_1.override = FireOutcomes.MISS
    fixture.fire_controls_2.override = FireOutcomes.PIN
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(7.5, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert unit.status == CombatUnit.Status.PINNED, "Target expects to be pinned"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_move) == True
    ), "PINNED reactive fire must maintain initiative for moving unit."


def test_one_pin_one_suppress(fixture: Fixture) -> None:
    fixture.fire_controls_1.override = FireOutcomes.PIN
    fixture.fire_controls_2.override = FireOutcomes.SUPPRESS
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(7.5, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert (
        unit.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be suppressed"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_move) == False
    ), "SUPPRESS reactive fire lose initiative for moving unit."


def test_both_suppress(fixture: Fixture) -> None:
    fixture.fire_controls_1.override = FireOutcomes.SUPPRESS
    fixture.fire_controls_2.override = FireOutcomes.SUPPRESS
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.try_component(fixture.unit_move, Transform)
    assert transform == None, "Target expects to be killed"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot_1) == True
    ), "KILL reactive fire lose initiative for moving unit."
