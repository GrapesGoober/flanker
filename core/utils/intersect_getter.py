from itertools import pairwise

import numpy as np
from numba import njit  # type: ignore
from numpy.typing import NDArray

from core.models.vec2 import Vec2


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

        # Prepare edge vertices and vectors
        edges: list[list[float]] = []
        edge_vectors: list[list[float]] = []
        if len(polyline) < 2:
            return []
        for v1, v2 in pairwise(polyline):
            edges.append([v1.x, v1.y])
            delta = v2 - v1
            edge_vectors.append([delta.x, delta.y])

        # Run the optimised intersect getter
        # Note: Explicitly tell numpy that we're working with 2d vectors with z=0;
        # this prevents np.cross from freaking out
        line_vector = line[1] - line[0]
        intersections = IntersectGetter._njit_get_intersect(
            line_vert=np.array([line[0].x, line[0].y], dtype=np.float64),
            line_vector=np.array([line_vector.x, line_vector.y], dtype=np.float64),
            edge_verts=np.array(edges, dtype=np.float64),
            edge_vectors=np.array(edge_vectors, dtype=np.float64),
        )
        # Convert to Vec2
        points = [Vec2(float(x), float(y)) for x, y in intersections]
        # Filter out colocated intersection points if exists
        unique_points = [p for i, p in enumerate(points) if p not in points[:i]]
        return list(unique_points)

    @staticmethod
    @njit(cache=True)  # type: ignore
    def _njit_get_intersect(
        line_vert: NDArray[np.float64],
        line_vector: NDArray[np.float64],
        edge_verts: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """
        Private optimized intersect getter for `get_intersects`.
        Computes all line segment intersections between a line and a set of edges
        represented as linear Bezier curves Line = start + t * vector.
        Returns NDArray (N x 2) of intersection points.
        Note: might return duplicate points if edges share a vertex.
        """

        # Use a scalar cross2d, as opposed to np.cross that doesnt support 2D
        def cross2d(
            a: NDArray[np.float64], b: NDArray[np.float64]
        ) -> NDArray[np.float64]:
            return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]

        # Compute two parametric values t & u of intersect point
        denominator = cross2d(line_vector, edge_vectors)
        q1_p1 = edge_verts - line_vert
        t = cross2d(q1_p1, edge_vectors) / denominator
        u = cross2d(q1_p1, line_vector) / denominator
        parallel_mask = np.abs(denominator) <= 1e-9

        # There's intersection if t and u values are in bound [0, 1]
        intersect_mask = (~parallel_mask) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)

        # Calculate intersection points using P = start + t * line_vector
        t_valid = t[intersect_mask]
        intersection_points = line_vert + t_valid[:, None] * line_vector
        return intersection_points
