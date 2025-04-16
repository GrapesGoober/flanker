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


def test_move(game_state: GameState) -> None:
    gs = game_state

    # Grab the target unit to move
    res = gs.system(EventSystem).emit(
        RifleSquadGetInput(), response_type=RifleSquadGetInput.Response
    )
    unit_id = None
    for r in res:
        if r.position == Vec2(0, -10):
            unit_id = r.unit_id
    assert unit_id is not None, "Target unit at Vec2(0, -10) not found."

    # Perform move action
    res = gs.system(EventSystem).emit(
        MoveActionInput(unit_id=unit_id, position=Vec2(20, -10))
    )
    assert res == [], "MoveActionInput emit expects no response"

    # Check whether the unit moved to the target position
    res = gs.system(EventSystem).emit(
        RifleSquadGetInput(), response_type=RifleSquadGetInput.Response
    )
    unit_pos = None
    for r in res:
        if r.unit_id == unit_id:
            unit_pos = r.position
    assert unit_pos is not None, "Unit position not found for the given unit_id."
    assert (
        unit_pos - Vec2(7.6, -10)
    ).length() < 1e-9, "Target expects at Vec2(7.6, -10)"
