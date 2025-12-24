from itertools import pairwise
from numba import njit  # type: ignore
import numpy as np
from numpy.typing import NDArray
from core.utils.vec2 import Vec2


class IntersectGetter:
    """Utility to compute line segment intersections."""

    @staticmethod
    def is_inside(
        point: Vec2,
        vertices: list[Vec2],
    ) -> bool:
        """
        Checks whether a point is inside vertices.
        Assumes a closed loop that `vertices[-1] == vertices[0]`.
        """
        if len(vertices) <= 2:
            raise ValueError("`is_inside` need at least three vertices.")

        line_cast_to = Vec2(max(v.x for v in vertices) + 1, point.y)
        intersect_points = IntersectGetter.get_intersects(
            line=(point, line_cast_to),
            vertices=vertices,
        )
        return len(intersect_points) % 2 != 0

    @staticmethod
    def get_intersects(
        line: tuple[Vec2, Vec2],
        vertices: list[Vec2],
    ) -> list[Vec2]:
        """
        Returns intersection points between a line and a polyline.
        Assumes that if closed loop, the last vert `vertices[-1] == vertices[0]`.
        """

        # Prepare edge vertices and vectors
        edges: list[list[float]] = []
        edge_vectors: list[list[float]] = []
        if len(vertices) < 2:
            return []
        for v1, v2 in pairwise(vertices):
            edges.append([v1.x, v1.y, 0.0])
            delta = v2 - v1
            edge_vectors.append([delta.x, delta.y, 0.0])

        # Run the optimised intersect getter
        # Note: Explicitly tell numpy that we're working with 2d vectors with z=0;
        # this prevents np.cross from freaking out
        line_vector = line[1] - line[0]
        intersections = IntersectGetter._njit_get_intersect(
            line_vert=np.array([line[0].x, line[0].y, 0], dtype=np.float64),
            line_vector=np.array([line_vector.x, line_vector.y, 0], dtype=np.float64),
            edge_verts=np.array(edges, dtype=np.float64),
            edge_vectors=np.array(edge_vectors, dtype=np.float64),
        )
        # Convert to Vec2
        points = [Vec2(float(x), float(y)) for x, y in intersections]
        # Filter out colocated intersection points if exists
        unique_points = [p for i, p in enumerate(points) if p not in points[:i]]
        return list(unique_points)

    @staticmethod
    @njit
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
        # Compute two parametric values t & u of intersect point
        # TODO: why use np.cross? Wikipedia says use determinant matrix
        # Is this why we're passing z=0 to prevent np.cross from freaking out?
        # This might not be the correct way to do this.
        denominator = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_verts - line_vert
        t = np.cross(q1_p1, edge_vectors)[:, 2] / denominator
        u = np.cross(q1_p1, line_vector)[:, 2] / denominator
        parallel_mask = np.abs(denominator) <= 1e-9

        # There's intersection if t and u values are in bound [0, 1]
        intersect_mask = (~parallel_mask) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)

        # Calculate intersection points using P = start + t * line_vector
        # Only slice [:2] to grab x and y, ignore z=0
        t_valid = t[intersect_mask]
        intersection_points = line_vert[:2] + t_valid[:, None] * line_vector[:2]
        return intersection_points
