import numpy as np
from numpy.typing import NDArray


def line_of_sight(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    polygons: NDArray[np.float64],
) -> bool:
    """
    Check if the line from source to target intersects any polygon.

    Parameters:
        source: Array of shape (2,) representing the source point.
        target: Array of shape (2,) representing the target point.
        polygons: Array of shape (N, M, 2), where N is the number of polygons,
                  and M is the number of vertices per polygon.

    Returns:
        True if there is line of sight (no intersection), False otherwise.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)

    p1 = source
    p2 = target

    v0 = polygons
    v1 = np.roll(polygons, shift=-1, axis=1)

    q1 = v0.reshape(-1, 2)
    q2 = v1.reshape(-1, 2)

    r = p2 - p1
    s = q2 - q1

    r_cross_s = np.cross(r, s)
    q1_p1 = q1 - p1

    t = np.cross(q1_p1, s) / r_cross_s
    u = np.cross(q1_p1, r) / r_cross_s

    parallel = np.isclose(r_cross_s, 0)

    intersect_mask = (~parallel) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)

    return not np.any(intersect_mask)


# Define polygons (2 polygons, each with 4 vertices)
polygons = np.array(
    [
        [[1, 1], [3, 1], [3, 3], [1, 3]],
        [[5, 5], [7, 5], [7, 7], [5, 7]],
    ]
)

source = np.array([0, 0])
target = np.array([6, 1.9])

visible = line_of_sight(source, target, polygons)
print("Line of sight:", visible)
