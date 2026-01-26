from dataclasses import dataclass

import pytest
from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


@dataclass
class Fixture:
    vertices: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:
    transform = Transform(Vec2(141, 26))

    verts = [
        Vec2(0.0, 0.0),
        Vec2(-3.0, 10.0),
        Vec2(-16.0, 53.5),
        Vec2(-37.0, 85.0),
        Vec2(-41.5, 92.0),
        Vec2(-41.5, 96.0),
        Vec2(-38.0, 98.5),
        Vec2(-30.5, 96.5),
        Vec2(-15.0, 77.5),
        Vec2(-5.5, 59.5),
        Vec2(2.5, 36.5),
        Vec2(8.0, 15.0),
        Vec2(8.0, 7.0),
        Vec2(5.0, -1.0),
        Vec2(0.0, 0.0),
    ]

    return Fixture(LinearTransform.apply(verts, transform))


def test_is_inside_false(fixture: Fixture) -> None:
    is_inside = IntersectGetter.is_inside(Vec2(104, 25), fixture.vertices)
    assert is_inside == False, "The point lies outside of the polygon."
