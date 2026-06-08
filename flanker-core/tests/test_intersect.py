from dataclasses import dataclass

import pytest
from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


@dataclass
class Fixture:
    is_inside_polygon: list[Vec2]
    upper_triangle: list[Vec2]
    polygon_3: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:

    return Fixture(
        # This polygon is imitating a terrain bug
        is_inside_polygon=LinearTransform.apply(
            [
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
            ],
            Transform(Vec2(141, 26)),
        ),
        # These two polygons are for apex clip tests
        upper_triangle=[
            Vec2(10, 0),
            Vec2(15, 5),
            Vec2(5, 5),
            Vec2(10, 0),
        ],
        polygon_3=[
            Vec2(15, 0),
            Vec2(20, -5),
            Vec2(20, 5),
            Vec2(15, 0),
        ],
    )


def test_is_inside_false(fixture: Fixture) -> None:
    is_inside = IntersectGetter.is_inside(Vec2(104, 25), fixture.is_inside_polygon)
    assert is_inside == False, "The point lies outside of the polygon."


def test_intersect(fixture: Fixture) -> None:
    line_from = Vec2(0, 0)
    line_to = Vec2(100, 0)
    intersects = IntersectGetter.get_intersects(
        line=(line_from, line_to),
        polyline=fixture.upper_triangle,
    )
    assert len(intersects) == 0, "Expects no intersection for apex clipping"
    intersects = IntersectGetter.get_intersects(
        line=(line_from, line_to),
        polyline=fixture.polygon_3,
    )
    assert intersects == {
        Vec2(15, 0),
        Vec2(20, 0),
    }, "Expects two intersections for non-clipping polygon"
