from dataclasses import dataclass
import math

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
    unit_move_1: int
    unit_move_2: int
    unit_shoot: int
    fire_controls: FireControls


@pytest.fixture
def reactive_group_fixture() -> Fixture:
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
    # orient shooter toward the first mover so FOV allows reactive fire
    shooter_transform = gs.get_component(unit_shoot, Transform)
    mover_transform = gs.get_component(unit_move_1, Transform)
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta

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
        unit_move_1=unit_move_1,
        unit_move_2=unit_move_2,
        unit_shoot=unit_shoot,
        fire_controls=fire_controls,
    )


def test_group_move(reactive_group_fixture: Fixture) -> None:
    MoveSystem.group_move(
        reactive_group_fixture.gs,
        moves=[
            (reactive_group_fixture.unit_move_1, Vec2(5, -15)),
            (reactive_group_fixture.unit_move_2, Vec2(6, -14)),
        ],
    )
    transform = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_1, Transform
    )
    assert transform.position == Vec2(
        5, -15
    ), "Move action expects to not be interrupted"

    transform_2 = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_2, Transform
    )
    assert transform_2.position == Vec2(
        6, -14
    ), "Move action expects to not be interrupted"
    assert (
        InitiativeSystem.has_initiative(
            reactive_group_fixture.gs, reactive_group_fixture.unit_shoot
        )
        == False
    ), "NO reactive fire mustn't flip initiative."


def test_interrupt_success(reactive_group_fixture: Fixture) -> None:
    reactive_group_fixture.fire_controls.override = FireOutcomes.SUPPRESS
    MoveSystem.group_move(
        reactive_group_fixture.gs,
        moves=[
            (reactive_group_fixture.unit_move_1, Vec2(7, -10)),
            (reactive_group_fixture.unit_move_2, Vec2(7, -15)),
        ],
    )
    transform_1 = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_1, Transform
    )
    assert transform_1.position == Vec2(
        7, -10
    ), "First unit must not be interrupted at Vec2(7, -10)"
    transform_2 = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_2, Transform
    )
    assert transform_2.position == Vec2(
        6.25, -15
    ), "Second unit must be interrupted at Vec2(6.25, -15)"
    assert (
        InitiativeSystem.has_initiative(
            reactive_group_fixture.gs, reactive_group_fixture.unit_shoot
        )
        == False
    ), "Success group move doesn't flip initiative."


def test_interrupt_fail(reactive_group_fixture: Fixture) -> None:
    reactive_group_fixture.fire_controls.override = FireOutcomes.SUPPRESS
    MoveSystem.group_move(
        reactive_group_fixture.gs,
        moves=[
            (reactive_group_fixture.unit_move_1, Vec2(9, -10)),
            (reactive_group_fixture.unit_move_2, Vec2(9, -15)),
        ],
    )
    transform_1 = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_1, Transform
    )
    assert transform_1.position == Vec2(
        7.5, -10
    ), "First unit must be interrupted at Vec2(7.5, -10)"
    transform_2 = reactive_group_fixture.gs.get_component(
        reactive_group_fixture.unit_move_2, Transform
    )
    assert transform_2.position == Vec2(
        6.25, -15
    ), "Second unit must be interrupted at Vec2(6.25, -15)"
    assert (
        InitiativeSystem.has_initiative(
            reactive_group_fixture.gs, reactive_group_fixture.unit_shoot
        ) == True
    ), "Success group move doesn't flip initiative."
