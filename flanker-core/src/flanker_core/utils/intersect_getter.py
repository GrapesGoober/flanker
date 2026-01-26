import numpy as np
from flanker_core.models.vec2 import Vec2
from numba import njit  # type: ignore
from numpy.typing import NDArray


class IntersectGetter:
    """Utility to compute line segment intersections."""

    @staticmethod
    def is_inside(
        point: Vec2,
        polygon: list[Vec2],
    ) -> bool:
        """
        Checks whether a point is inside a polygon.
        Polygon must be closed loop that `polygon[-1] == polygon[0]`.
        """
        if len(polygon) <= 2:
            raise ValueError("`is_inside` need at least three vertices.")
        if polygon[-1] != polygon[0]:
            raise ValueError("Polygon is not closed loop.")

        # Create a line in arbitrary (right-ward) direction to count intersections
        # Direction doesn't matter. All results are the same.
        line_cast_to = Vec2(max(v.x for v in polygon) + 1, point.y)
        # Prevent this line from casting directly at a vertex
        line_cast_to = line_cast_to.rotated(1e-6)
        # Cast and count
        intersect_points = IntersectGetter.get_intersects(
            line=(point, line_cast_to),
            polyline=polygon,
        )
        return len(intersect_points) % 2 != 0

    @staticmethod
    def get_intersects(
        line: tuple[Vec2, Vec2],
        polyline: list[Vec2],
    ) -> list[Vec2]:
        """
        Returns intersection points between a line and a polyline.
        For a closed loop, the vertices must repeat `polyline[-1] == polyline[0]`.
        """

        if len(polyline) < 2:
            return []

        # Convert to np arrays and let the compiled function compute
        intersections = IntersectGetter._njit_get_intersect(
            line_start=np.array([line[0].x, line[0].y], dtype=np.float64),
            line_end=np.array([line[1].x, line[1].y], dtype=np.float64),
            polyline=np.array([[v.x, v.y] for v in polyline], dtype=np.float64),
        )
        # Convert to Vec2
        points = [Vec2(float(x), float(y)) for x, y in intersections]
        # Filter out colocated intersection points if exists
        unique_points = [p for i, p in enumerate(points) if p not in points[:i]]
        return list(unique_points)

    @staticmethod
    @njit(cache=True)  # type: ignore
    def _njit_get_intersect(
        line_start: NDArray[np.float64],
        line_end: NDArray[np.float64],
        polyline: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """
        Private optimized intersect getter for `get_intersects`.
        Takes line_start, line_end, and polyline (Nx2 array of vertices).
        Computes all line segment intersections between the line and polyline edges.
        Note: might return duplicate points if edges share a vertex.
        Returns NDArray (M x 2) of intersection points.
        """

        # Use a scalar cross2d, as opposed to np.cross that doesnt support 2D
        def cross2d(
            a: NDArray[np.float64], b: NDArray[np.float64]
        ) -> NDArray[np.float64]:
            return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]

        # Need a line vector for a linear bezier line
        # Linear Bezier Equation: line = start + t * vector
        line_vector = line_end - line_start

        # Need bezier edge vectors from polyline
        n_edges = polyline.shape[0] - 1
        if n_edges < 1:  # No edges, no intersections
            return np.empty((0, 2), dtype=np.float64)
        edge_verts = polyline[:-1]
        edge_ends = polyline[1:]
        edge_vectors = edge_ends - edge_verts

        # Calculate the denominator and filter out parallel edges
        denominator = cross2d(line_vector, edge_vectors)
        non_parallel_mask = np.abs(denominator) >= 1e-9
        edge_vectors = edge_vectors[non_parallel_mask]
        edge_verts = edge_verts[non_parallel_mask]
        denominator = denominator[non_parallel_mask]

        # Compute two parametric values t & u of intersect point
        q1_p1 = edge_verts - line_start
        t = cross2d(q1_p1, edge_vectors) / denominator
        u = cross2d(q1_p1, line_vector) / denominator

        # There's intersection if t and u values are in bound [0, 1]
        intersect_mask = (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)

        # Calculate intersection points using P = start + t * line_vector
        t_valid = t[intersect_mask]
        intersection_points = line_start + t_valid[:, None] * line_vector
        return intersection_points
