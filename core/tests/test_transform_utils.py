from core.models.components import Transform
from core.models.vec2 import Vec2
from core.utils.linear_transform import LinearTransform


def test_translate() -> None:
    vecs = [Vec2(1, 2), Vec2(-3, 4)]
    offset = Vec2(2, -1)
    result = LinearTransform.translate(vecs, offset)
    assert result == [Vec2(3, 1), Vec2(-1, 3)]


def test_rotate() -> None:
    vecs = [Vec2(1, 0), Vec2(0, 1)]
    angle = 90
    result = LinearTransform.rotate(vecs, angle)
    assert result == [Vec2(0.0, 1), Vec2(-1, 0.0)]


def test_apply() -> None:
    vecs = [Vec2(1, 0), Vec2(0, 1)]
    transform = Transform(position=Vec2(1, 1), degrees=90)
    result = LinearTransform.apply(vecs, transform)
    assert result == [Vec2(x=1.0, y=2.0), Vec2(x=0.0, y=1.0)]
