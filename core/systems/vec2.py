from dataclasses import dataclass
from math import sqrt


@dataclass
class Vec2:
    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __rsub__(self, other: "Vec2") -> "Vec2":
        return Vec2(other.x - self.x, other.y - self.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def cross(self, other: "Vec2") -> float:
        return self.x * other.y - self.y * other.x

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return sqrt(self.x**2 + self.y**2)

    def normalized(self) -> "Vec2":
        length = self.length()
        return self / length if length else Vec2(0, 0)
