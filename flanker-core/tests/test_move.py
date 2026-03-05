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


# pylint: disable=redefined-outer-name

def test_move(fixture: Fixture) -> None:
    """Movement causes position update and heading pivot."""
    # starting orientation 0, moving down-right should pivot to ~296 degrees
    MoveSystem.move(fixture.gs, fixture.unit_id_1, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"
    # check pivoted heading
    # compute expected heading manually
    dx, dy = 5 - 0, -15 - (-10)
    expected = (180 / math.pi) * math.atan2(dy, dx)
    if expected < 0:
        expected += 360
    assert abs(transform.degrees - expected) < 1e-6, "Unit should pivot toward movement"


# pylint: disable=redefined-outer-name

def test_move_invalid(fixture: Fixture) -> None:
    """Invalid move should leave position unchanged."""
    MoveSystem.move(fixture.gs, fixture.unit_id_1, Vec2(6, 6))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform.position == Vec2(0, -10), "Unit #1 expects to not move"


# pylint: disable=redefined-outer-name

def test_move_fov_reactive(fixture: Fixture) -> None:
    """A clear-line spotter behind and facing away should not interrupt.

    The original fixture includes terrain which sometimes blocks LOS; to make
    this assertion meaningful we place the spotter on the same horizontal band
    as the moving unit so that LOS is unobstructed.  The spotter's heading is
    deliberately set to point *away* from the mover, so FOV filtering should
    prevent any reactive fire from occurring even though an interruption would
    otherwise be possible.
    """
    _spotter_id = fixture.gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(1, -10), degrees=0),  # spotter east of mover, facing east
    )
    # ensure blue has initiative
    InitiativeSystem.set_initiative(fixture.gs, InitiativeState.Faction.BLUE)
    MoveSystem.move(fixture.gs, fixture.unit_id_1, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform.position == Vec2(5, -15), "movement should complete despite spotter"


# pylint: disable=redefined-outer-name

def test_group_move(fixture: Fixture) -> None:
    """Group move applies both movement and pivot to each unit."""
    # group move should also pivot each unit
    MoveSystem.group_move(
        fixture.gs,
        moves=[
            (fixture.unit_id_1, Vec2(5, -15)),
            (fixture.unit_id_2, Vec2(15, -5)),
        ],
    )
    transform_1 = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform_1.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"

    transform_2 = fixture.gs.get_component(fixture.unit_id_2, Transform)
    assert transform_2.position == Vec2(15, -5), "Unit #2 expects at Vec2(15, -5)"
