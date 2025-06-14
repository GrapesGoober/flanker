from dataclasses import dataclass
from math import sqrt, isclose


@dataclass
class Vec2:
    """2D vector class for basic vector operations"""

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
        """Returns a cross product with another vector."""
        return self.x * other.y - self.y * other.x

    def dot(self, other: "Vec2") -> float:
        """Returns a dot product with another vector."""
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        """Returns a length (norm) of this vector."""
        return sqrt(self.x**2 + self.y**2)

    def normalized(self) -> "Vec2":
        """Returns a new normalized vector."""
        length = self.length()
        return self / length if length else Vec2(0, 0)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec2):
            return NotImplemented
        x_close = isclose(self.x, other.x, abs_tol=1e-9)
        y_close = isclose(self.y, other.y, abs_tol=1e-9)
        return x_close and y_close
