import matplotlib.pyplot as plt

from core.models.components import Transform
from core.models.vec2 import Vec2
from core.utils.linear_transform import LinearTransform

# Original vertices
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
]

# Transform
transform = Transform(Vec2(141, 26))
verts_transformed = LinearTransform.apply(verts, transform)

# Convert to x, y lists for plotting
x = [v.x for v in verts_transformed] + [verts_transformed[0].x]
y = [v.y for v in verts_transformed] + [verts_transformed[0].y]

# Point to compare
points = [
    Vec2(104, 25),
    Vec2(146, 25),
]

plt.figure(figsize=(8, 8))  # type: ignore
plt.plot(x, y, "b-", label="Polygon")  # type: ignore
plt.fill(x, y, alpha=0.2)  # type: ignore
for point in points:
    point_str = f"({point.x}, {point.y})"
    plt.plot(point.x, point.y, "ro", label=f"Point {point_str}")  # type: ignore
    plt.text(point.x, point.y, point_str, fontsize=12, ha="right")  # type: ignore
plt.axis("equal")  # type: ignore
plt.legend()  # type: ignore
plt.title("Transformed Polygon and Point (104, 25)")  # type: ignore
plt.xlabel("X")  # type: ignore
plt.ylabel("Y")  # type: ignore
plt.grid(True)  # type: ignore
plt.show()  # type: ignore
