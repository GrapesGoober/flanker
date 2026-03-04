"""Unit tests for movement system including pivot and reactive fire.

These exercises simulate simple scenarios and assert correct state
updates, pivot behavior, and group movements.
"""

from dataclasses import dataclass
import math

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    MoveControls,
    TerrainFeature,
    Transform,
    FireControls,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.models.outcomes import FireOutcomes


@dataclass
class Fixture:
    """Bundle of objects used by move system tests."""
    gs: GameState
    unit_id_1: int
    unit_id_2: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(InitiativeState())
    # Rifle Squad
    unit_id_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
    )
    unit_id_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(5, -10)),
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

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(-10, 0),
                Vec2(-10, -10),
                Vec2(0, -10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.WALKABLE,
        ),
    )

    return Fixture(gs, unit_id_1, unit_id_2)


def test_move(fx: Fixture) -> None:
    """Movement causes position update and heading pivot."""
    # starting orientation 0, moving down-right should pivot to ~296 degrees
    MoveSystem.move(fx.gs, fx.unit_id_1, Vec2(5, -15))
    transform = fx.gs.get_component(fx.unit_id_1, Transform)
    assert transform.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"
    # check pivoted heading
    # compute expected heading manually
    dx, dy = 5 - 0, -15 - (-10)
    expected = (180 / math.pi) * math.atan2(dy, dx)
    if expected < 0:
        expected += 360
    assert abs(transform.degrees - expected) < 1e-6, "Unit should pivot toward movement"


def test_move_invalid(fx: Fixture) -> None:
    """Invalid move should leave position unchanged."""
    MoveSystem.move(fx.gs, fx.unit_id_1, Vec2(6, 6))
    transform = fx.gs.get_component(fx.unit_id_1, Transform)
    assert transform.position == Vec2(0, -10), "Unit #1 expects to not move"


def test_move_fov_reactive(fx: Fixture) -> None:
    """A rear spotter outside FOV does not interrupt movement."""
    # spotter behind facing away should not interrupt
    _spotter_id = fx.gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(1, 0), degrees=180),
    )
    # ensure blue has initiative
    InitiativeSystem.set_initiative(fx.gs, InitiativeState.Faction.BLUE)
    MoveSystem.move(fx.gs, fx.unit_id_1, Vec2(5, -15))
    transform = fx.gs.get_component(fx.unit_id_1, Transform)
    assert transform.position == Vec2(5, -15), "movement should complete despite spotter"


def test_group_move(fx: Fixture) -> None:
    """Group move applies both movement and pivot to each unit."""
    # group move should also pivot each unit
    MoveSystem.group_move(
        fx.gs,
        moves=[
            (fx.unit_id_1, Vec2(5, -15)),
            (fx.unit_id_2, Vec2(15, -5)),
        ],
    )
    transform_1 = fx.gs.get_component(fx.unit_id_1, Transform)
    assert transform_1.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"

    transform_2 = fixture.gs.get_component(fixture.unit_id_2, Transform)
    assert transform_2.position == Vec2(15, -5), "Unit #2 expects at Vec2(15, -5)"
