from typing import Callable
import pytest
from domain.interface import MoveActionInput, RifleSquadGetInput
from domain.rifle_squad import RifleSquad
from systems.ecs import Entity, GameState
from systems.event import EventSystem
from systems.polygon import Polygon, PolygonSpace
from systems.vec2 import Vec2


@pytest.fixture
def game_state() -> GameState:
    gs = GameState(EventSystem(), PolygonSpace())
    gs.add(
        Entity(
            gs,
            Polygon(
                [
                    Vec2(0, 0),
                    Vec2(10, 0),
                    Vec2(10, 10),
                    Vec2(0, 10),
                    Vec2(0, 0),
                ]
            ),
        ),
        RifleSquad(gs, Vec2(0, -10)),
        RifleSquad(gs, Vec2(15, 20)),
    )
    return gs


def get_unit_response(
    gs: GameState, condition: Callable[[RifleSquadGetInput.Response], bool]
) -> RifleSquadGetInput.Response:
    res = gs.system(EventSystem).emit(
        RifleSquadGetInput(), response_type=RifleSquadGetInput.Response
    )
    unit_res = None
    for r in res:
        if condition(r):
            unit_res = r
    assert unit_res is not None, "Target unit not found."
    return unit_res


def test_move(game_state: GameState) -> None:
    gs = game_state

    # Grab the target unit to move
    res = get_unit_response(gs, lambda r: r.position == Vec2(0, -10))

    # Perform move action
    gs.system(EventSystem).emit(
        MoveActionInput(unit_id=res.unit_id, position=Vec2(5, -15))
    )

    # Check whether the unit moved to the target position
    res = get_unit_response(gs, lambda r: r.unit_id == res.unit_id)
    assert (
        res.position - Vec2(5, -15)
    ).length() < 1e-9, "Target expects at Vec2(7.6, -10)"


def test_los_interrupt(game_state: GameState) -> None:
    gs = game_state
    res = get_unit_response(gs, lambda r: r.position == Vec2(0, -10))

    gs.system(EventSystem).emit(
        MoveActionInput(unit_id=res.unit_id, position=Vec2(20, -10))
    )

    res = get_unit_response(gs, lambda r: r.unit_id == res.unit_id)
    assert (
        res.position - Vec2(7.6, -10)
    ).length() < 1e-9, "Target expects at Vec2(7.6, -10)"
