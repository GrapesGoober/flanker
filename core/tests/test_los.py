import pytest
import esper

from components import MovementControls, TerrainFeature, Transform, UnitCondition
from move_action import MoveAction
from terrain_types import TerrainType, to_flags
from vec2 import Vec2


@pytest.fixture
def game_state() -> tuple[int, Transform, UnitCondition]:
    esper.clear_database()
    # Rifle Squads
    esper.create_entity(
        Transform(position=Vec2(15, 20)), MovementControls(), UnitCondition()
    )
    id = esper.create_entity(
        unit_pos := Transform(position=Vec2(0, -10)),
        MovementControls(),
        unit_cond := UnitCondition(),
    )
    # 10x10 opaque box
    esper.create_entity(
        Transform(position=Vec2(0, 0)),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
                Vec2(0, 0),
            ],
            flag=to_flags(TerrainType.FOREST),
        ),
    )

    return id, unit_pos, unit_cond


def test_move(game_state: tuple[int, Transform, UnitCondition]) -> None:
    id, unit_pos, _ = game_state
    MoveAction.move(id, Vec2(5, -15))
    assert unit_pos.position == Vec2(5, -15), "Target expects at Vec2(5, -15)"


def test_los_interrupt(game_state: tuple[int, Transform, UnitCondition]) -> None:
    id, unit_pos, unit_cond = game_state
    MoveAction.move(id, Vec2(20, -10))
    assert unit_pos.position == Vec2(7.6, -10), "Target expects at Vec2(7.6, -10)"
    assert (
        unit_cond.status == UnitCondition.status.SUPPRESSED
    ), "Target expects to be suppressed"
