import math
from core.vec2 import Vec2
from core.transform_utils import TransformUtils


def test_offset() -> None:
    vecs = [Vec2(1, 2), Vec2(-3, 4)]
    offset = Vec2(2, -1)
    result = TransformUtils.offset(vecs, offset)
    assert result == [Vec2(3, 1), Vec2(-1, 3)]


def test_rotate() -> None:
    vecs = [Vec2(1, 0), Vec2(0, 1)]
    angle = math.pi / 2  # 90 degrees
    result = TransformUtils.rotate(vecs, angle)
    assert result == [Vec2(0, 1), Vec2(-1, 0)]
