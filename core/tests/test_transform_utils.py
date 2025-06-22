from core.components import Transform
from core.vec2 import Vec2
from core.transform_utils import TransformUtils


def test_translate() -> None:
    vecs = [Vec2(1, 2), Vec2(-3, 4)]
    offset = Vec2(2, -1)
    result = TransformUtils.translate(vecs, offset)
    assert result == [Vec2(3, 1), Vec2(-1, 3)]


def test_rotate() -> None:
    vecs = [Vec2(1, 0), Vec2(0, 1)]
    angle = 90
    result = TransformUtils.rotate(vecs, angle)
    assert result == [Vec2(0.0, 1), Vec2(-1, 0.0)]


def test_apply() -> None:
    vecs = [Vec2(1, 0), Vec2(0, 1)]
    transform = Transform(position=Vec2(1, 1), angle=90)
    result = TransformUtils.apply(vecs, transform)
    assert result == [Vec2(x=1.0, y=2.0), Vec2(x=0.0, y=1.0)]
