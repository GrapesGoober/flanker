from typing import Callable
from unittest import TestCase, main

from systems.ecs import Entity, GameState
from systems.event import EventSystem, Listener
from systems.polygon import PolygonSpace


class TestEvents(TestCase):
    def test_event_call(self) -> None:

        gs = GameState(EventSystem(), PolygonSpace())

        int_callback: Callable[[int], int] = lambda x: x + 10
        str_callback: Callable[[str], str] = lambda x: x + "defg"

        gs.add(
            Entity(gs, Listener(int, int_callback)),
            Entity(gs, Listener(str, str_callback)),
            Entity(gs, Listener(str, str_callback)),
            Entity(gs, Listener(int, int_callback)),
        )

        res = gs.system(EventSystem).emit(3)
        self.assertEqual(res, [], "Untyped response must return []")
        res = gs.system(EventSystem).emit("str")
        self.assertEqual(res, [], "Untyped response must return []")
        res = gs.system(EventSystem).emit("str", int)
        self.assertEqual(res, [], "Mistyped response must return []")

        res = gs.system(EventSystem).emit(3, int)
        self.assertEqual(len(res), 2, "Expected two int responses")
        self.assertEqual(res, [13, 13], "Incorrect response value")

        res = gs.system(EventSystem).emit("abc", str)
        self.assertEqual(len(res), 2, "Expected two str responses")
        self.assertEqual(res, ["abcdefg"] * 2, "Incorrect response value")


if __name__ == "__main__":
    main()
