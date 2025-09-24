from dataclasses import dataclass
import pytest

from core.action_models import GroupMoveAction, MoveAction
from core.components import (
    InitiativeState,
    MoveControls,
    TerrainFeature,
    CombatUnit,
)
from core.gamestate import GameState
from core.systems.los_system import Transform
from core.systems.move_system import LoggingSystem, MoveSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
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


def test_move(fixture: Fixture) -> None:
    result_log = MoveSystem.move(
        fixture.gs, MoveAction(fixture.unit_id_1, Vec2(5, -15))
    )
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert LoggingSystem.get_logs(fixture.gs) == [
        result_log
    ], "Expects move result to be logged"
    assert transform.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"


def test_move_invalid(fixture: Fixture) -> None:
    result_log = MoveSystem.move(fixture.gs, MoveAction(fixture.unit_id_1, Vec2(6, 6)))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert LoggingSystem.get_logs(fixture.gs) == [
        result_log
    ], "Expects move result to be logged"
    assert transform.position == Vec2(0, -10), "Unit #1 expects to not move"


def test_group_move(fixture: Fixture) -> None:
    result_log = MoveSystem.group_move(
        fixture.gs,
        GroupMoveAction(
            moves=[
                MoveAction(fixture.unit_id_1, Vec2(5, -15)),
                MoveAction(fixture.unit_id_2, Vec2(15, -5)),
            ]
        ),
    )
    assert LoggingSystem.get_logs(fixture.gs) == [
        result_log
    ], "Expects move result to be logged"

    transform_1 = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform_1.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"

    transform_2 = fixture.gs.get_component(fixture.unit_id_2, Transform)
    assert transform_2.position == Vec2(15, -5), "Unit #2 expects at Vec2(15, -5)"
