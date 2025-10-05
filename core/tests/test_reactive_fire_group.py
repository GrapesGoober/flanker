from dataclasses import dataclass
import pytest

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
    unit_move_1: int
    unit_move_2: int
    unit_shoot: int
    fire_controls: FireControls


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    unit_move_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
    )
    unit_move_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -15)),
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

    return Fixture(
        gs=gs,
        unit_move_1=unit_move_1,
        unit_move_2=unit_move_2,
        unit_shoot=unit_shoot,
        fire_controls=fire_controls,
    )


def test_group_move(fixture: Fixture) -> None:
    MoveSystem.group_move(
        fixture.gs,
        moves=[
            (fixture.unit_move_1, Vec2(5, -15)),
            (fixture.unit_move_2, Vec2(6, -14)),
        ],
    )
    transform = fixture.gs.get_component(fixture.unit_move_1, Transform)
    assert transform.position == Vec2(
        5, -15
    ), "Move action expects to not be interrupted"

    transform_2 = fixture.gs.get_component(fixture.unit_move_2, Transform)
    assert transform_2.position == Vec2(
        6, -14
    ), "Move action expects to not be interrupted"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == False
    ), "NO reactive fire mustn't flip initiative."


def test_interrupt_success(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.SUPPRESS
    MoveSystem.group_move(
        fixture.gs,
        moves=[
            (fixture.unit_move_1, Vec2(7, -10)),
            (fixture.unit_move_2, Vec2(7, -15)),
        ],
    )
    transform_1 = fixture.gs.get_component(fixture.unit_move_1, Transform)
    assert transform_1.position == Vec2(
        7, -10
    ), "First unit must not be interrupted at Vec2(7, -10)"
    transform_2 = fixture.gs.get_component(fixture.unit_move_2, Transform)
    assert transform_2.position == Vec2(
        7, -15
    ), "Second unit must be interrupted at Vec2(7, -15)"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == False
    ), "Success group move doesn't flip initiative."


def test_interrupt_fail(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.SUPPRESS
    MoveSystem.group_move(
        fixture.gs,
        moves=[
            (fixture.unit_move_1, Vec2(9, -10)),
            (fixture.unit_move_2, Vec2(9, -15)),
        ],
    )
    transform_1 = fixture.gs.get_component(fixture.unit_move_1, Transform)
    assert transform_1.position == Vec2(
        8, -10
    ), "First unit must not be interrupted at Vec2(8, -10)"
    transform_2 = fixture.gs.get_component(fixture.unit_move_2, Transform)
    assert transform_2.position == Vec2(
        7, -15
    ), "Second unit must be interrupted at Vec2(7, -15)"
    assert (
        InitiativeSystem.has_initiative(fixture.gs, fixture.unit_shoot) == True
    ), "Success group move doesn't flip initiative."
