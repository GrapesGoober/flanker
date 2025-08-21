import numpy as np
from numpy.typing import NDArray


def line_of_sight(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    polygons: NDArray[np.float64],
) -> bool:
    """Check if the line from source to target intersects any polygon."""

    # Ensure two points are float points for a single line vector
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    line_vector = target - source

    # Create a vector of edges
    shifted_polygons = np.roll(polygons, shift=-1, axis=1)
    edge_source = polygons.reshape(-1, 2)
    edge_target = shifted_polygons.reshape(-1, 2)
    edge_vectors = edge_target - edge_source

    # Compute two parametric values t & u of intersect point
    line_cross_edge = np.cross(line_vector, edge_vectors)
    q1_p1 = edge_source - source
    t = np.cross(q1_p1, edge_vectors) / line_cross_edge
    u = np.cross(q1_p1, line_vector) / line_cross_edge

    parallel = np.isclose(line_cross_edge, 0)
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
target = np.array([6, 1.999])

visible = line_of_sight(source, target, polygons)
print("Line of sight:", visible)
