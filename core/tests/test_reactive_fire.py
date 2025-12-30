from dataclasses import dataclass
import pytest

from core.action_models import FireOutcomes, MoveAction
from core.components import (
    InitiativeState,
    FireControls,
    MoveControls,
    TerrainFeature,
    CombatUnit,
    Transform,
)
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.move_system import MoveSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_move: int
    unit_friendly: int
    unit_shoot: int
    fire_controls: FireControls


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
    unit_friendly = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -11)),
    )
    unit_shoot = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        fire_controls := FireControls(),
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
    # 200x200 boundary
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
        unit_friendly=unit_friendly,
        unit_shoot=unit_shoot,
        fire_controls=fire_controls,
    )


def test_move(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, MoveAction(fixture.unit_move, Vec2(5, -15)))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        5, -15
    ), "Move action expects to not be interrupted"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == False
    ), "NO reactive fire mustn't flip initiative."


def test_interrupt_miss(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.MISS
    MoveSystem.move(fixture.gs, MoveAction(fixture.unit_move, Vec2(20, -10)))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        20, -10
    ), "Move action expects to not be interrupted"
    fire_controls = fixture.gs.get_component(fixture.unit_shoot, FireControls)
    assert (
        fire_controls.can_reactive_fire == False
    ), "MISS reactive fire results in NO FIRE"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == False
    ), "MISS reactive fire mustn't flip initiative"
    InitiativeSystem.flip_initiative(fixture.gs)
    assert (
        fire_controls and fire_controls.can_reactive_fire == True
    ), "Passing initiative must reset reactive fire"


def test_interrupt_pin(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.PIN
    MoveSystem.move(fixture.gs, MoveAction(fixture.unit_move, Vec2(20, -10)))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(7.5, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert unit.status == CombatUnit.Status.PINNED, "Target expects to be pinned"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == False
    ), "PINNED reactive fire must maintain initiative."
    assert (
        fixture.fire_controls.can_reactive_fire == True
    ), "PINNED reactive fire doesn't mark shooter as NO FIRE"


def test_interrupt_suppress(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.SUPPRESS
    MoveSystem.move(fixture.gs, MoveAction(fixture.unit_move, Vec2(20, -10)))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(8, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert (
        unit.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be suppressed"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == True
    ), "SUPPRESS reactive fire must flip initiative."


def test_interrupt_kill(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireOutcomes.KILL
    MoveSystem.move(fixture.gs, MoveAction(fixture.unit_move, Vec2(20, -10)))
    transform = fixture.gs.try_component(fixture.unit_move, Transform)
    assert transform == None, "Target expects to be killed"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == True
    ), "KILL reactive fire must flip initiative"
