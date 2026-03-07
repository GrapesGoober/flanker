from dataclasses import dataclass

import pytest
from flanker_ai.ai_agent import MoveSystem
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


@dataclass
class Fixture:
    gs: GameState
    unit_move: int
    unit_shoot: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    unit_move = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, 0)),
    )
    unit_shoot = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(
            position=Vec2(20, 10),
            degrees=-90,
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
        unit_shoot=unit_shoot,
    )


def test_reactive_fire_at_fov(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, 0))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform.position == Vec2(
        10, 0
    ), "Expects to be interrupted at FOV border (10, 0)."


def test_reactive_fire_after_rotated(fixture: Fixture) -> None:
    # Rotate the RED unit slightly to the left so that FOV is 56.31 degrees
    red_transform = fixture.gs.get_component(fixture.unit_shoot, Transform)
    red_transform.degrees = -101.31
    MoveSystem.move(fixture.gs, fixture.unit_move, Vec2(20, 0))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert (
        transform.position - Vec2(5, 0)
    ).length() < 1e-2, "Expects to be interrupted at FOV border (5, 0)."
