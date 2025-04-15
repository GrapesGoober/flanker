from typing import Callable
from unittest import TestCase

from systems.ecs import Entity, GameState
from systems.event import EventSystem, Listener
from systems.polygon import PolygonSpace


class SingleGameState(TestCase):

    def setUp(self) -> None:
        self.gs = GameState(EventSystem(), PolygonSpace())

        int_callback: Callable[[int], int] = lambda x: x + 10
        str_callback: Callable[[str], str] = lambda x: x + "defg"

        self.gs.add(
            Entity(self.gs, Listener(int, int_callback)),
            Entity(self.gs, Listener(str, str_callback)),
            Entity(self.gs, Listener(str, str_callback)),
            Entity(self.gs, Listener(int, int_callback)),
        )

    def test_untyped_emit(self) -> None:
        res = self.gs.system(EventSystem).emit(3)
        self.assertEqual(res, [], "Untyped emit expects no response")
        res = self.gs.system(EventSystem).emit("str")
        self.assertEqual(res, [], "Untyped emit expects no response")
        res = self.gs.system(EventSystem).emit("str", int)
        self.assertEqual(res, [], "Mistyped emit expects no response")

    def test_typed_emit(self) -> None:
        res = self.gs.system(EventSystem).emit(3, int)
        self.assertEqual(res, [13, 13], "Typed emit expects responses")

        res = self.gs.system(EventSystem).emit("abc", str)
        self.assertEqual(res, ["abcdefg"] * 2, "Typed emit expects responses")


class MultiGameState(TestCase):

    def setUp(self) -> None:
        self.gs1 = GameState(EventSystem(), PolygonSpace())
        self.gs2 = GameState(EventSystem(), PolygonSpace())

        int_callback: Callable[[int], int] = lambda x: x + 10
        str_callback: Callable[[str], str] = lambda x: x + "defg"

        self.gs1.add(
            Entity(self.gs1, Listener(int, int_callback)),
            Entity(self.gs1, Listener(int, int_callback)),
        )
        self.gs2.add(
            Entity(self.gs1, Listener(str, str_callback)),
            Entity(self.gs1, Listener(str, str_callback)),
        )

    def test_untyped_emit(self) -> None:

        res = self.gs1.system(EventSystem).emit(3)
        self.assertEqual(res, [], "Untyped emit expects no response")
        res = self.gs1.system(EventSystem).emit("str")
        self.assertEqual(res, [], "Untyped emit expects no response")
        res = self.gs1.system(EventSystem).emit("str", int)
        self.assertEqual(res, [], "Mistyped emit expects no response")

    def test_multi_gs(self) -> None:

        res = self.gs1.system(EventSystem).emit(3, int)
        self.assertEqual(res, [13, 13], "Typed emit expects responses")
        res = self.gs1.system(EventSystem).emit("abc", str)
        self.assertEqual(res, [], "Expects no listeners")

        res = self.gs2.system(EventSystem).emit("abc", str)
        self.assertEqual(res, ["abcdefg"] * 2, "Typed emit expects responses")
        res = self.gs2.system(EventSystem).emit(3, int)
        self.assertEqual(res, [], "Expects no listeners")
