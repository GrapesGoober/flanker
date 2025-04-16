import pytest
from typing import Callable
from systems.ecs import Entity, GameState
from systems.event import EventSystem, Listener
from systems.polygon import PolygonSpace


@pytest.fixture
def single_game_state() -> GameState:
    gs = GameState(EventSystem(), PolygonSpace())

    int_callback: Callable[[int], int] = lambda x: x + 10
    str_callback: Callable[[str], str] = lambda x: x + "defg"

    gs.add(
        Entity(gs, Listener(int, int_callback)),
        Entity(gs, Listener(str, str_callback)),
        Entity(gs, Listener(str, str_callback)),
        Entity(gs, Listener(int, int_callback)),
    )
    return gs


def test_untyped_emit_single(single_game_state: GameState) -> None:
    gs = single_game_state
    res = gs.system(EventSystem).emit(3)
    assert res == [], "Untyped emit expects no response"
    res = gs.system(EventSystem).emit("str")
    assert res == [], "Untyped emit expects no response"
    res = gs.system(EventSystem).emit("str", int)
    assert res == [], "Mistyped emit expects no response"


def test_typed_emit_single(single_game_state: GameState) -> None:
    gs = single_game_state
    res = gs.system(EventSystem).emit(3, int)
    assert res == [13, 13], "Typed emit expects responses"

    res = gs.system(EventSystem).emit("abc", str)
    assert res == ["abcdefg"] * 2, "Typed emit expects responses"


@pytest.fixture
def multi_game_state() -> tuple[GameState, GameState]:
    gs1 = GameState(EventSystem(), PolygonSpace())
    gs2 = GameState(EventSystem(), PolygonSpace())

    int_callback: Callable[[int], int] = lambda x: x + 10
    str_callback: Callable[[str], str] = lambda x: x + "defg"

    gs1.add(
        Entity(gs1, Listener(int, int_callback)),
        Entity(gs1, Listener(int, int_callback)),
    )
    gs2.add(
        Entity(gs2, Listener(str, str_callback)),
        Entity(gs2, Listener(str, str_callback)),
    )
    return gs1, gs2


def test_untyped_emit_multi(multi_game_state: tuple[GameState, GameState]) -> None:
    gs1, _ = multi_game_state

    res = gs1.system(EventSystem).emit(3)
    assert res == [], "Untyped emit expects no response"
    res = gs1.system(EventSystem).emit("str")
    assert res == [], "Untyped emit expects no response"
    res = gs1.system(EventSystem).emit("str", int)
    assert res == [], "Mistyped emit expects no response"


def test_multi_gs(multi_game_state: tuple[GameState, GameState]) -> None:
    gs1, gs2 = multi_game_state

    res = gs1.system(EventSystem).emit(3, int)
    assert res == [13, 13], "Typed emit expects responses"
    res = gs1.system(EventSystem).emit("abc", str)
    assert res == [], "Expects no listeners"

    res = gs2.system(EventSystem).emit("abc", str)
    assert res == ["abcdefg"] * 2, "Typed emit expects responses"
    res = gs2.system(EventSystem).emit(3, int)
    assert res == [], "Expects no listeners"
