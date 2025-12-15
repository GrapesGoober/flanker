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

        line_cast_to = Vec2(max(v.x for v in vertices) + 1, point.y)
        # TODO: it thinks it's inside one terrain entity
        # PROVE: try changing the source point by 0.1
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
        intersections = IntersectGetter._njit_get_intersect(
            start_pos=(line[0].x, line[0].y),
            end_pos=(line[1].x, line[1].y),
            edge_verts=np.array(edges, dtype=np.float64),
            edge_vectors=np.array(edge_vectors, dtype=np.float64),
        )
        # Convert to Vec2
        points = [Vec2(x, y) for x, y in intersections]
        # Filter out colocated points using Vec2 equality
        unique_points = [p for i, p in enumerate(points) if p not in points[:i]]
        return list(unique_points)

    @staticmethod
    @njit
    def _njit_get_intersect(
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
        edge_verts: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Returns NDArray of intersection coordinates (N x 2)."""
        # Explicitly tell numpy that we're working with 2d vectors with z=0;
        # this prevents np.cross from freaking out
        start = np.array([start_pos[0], start_pos[1], 0], dtype=np.float64)
        end = np.array([end_pos[0], end_pos[1], 0], dtype=np.float64)
        line_vector = end - start

        # Compute two parametric values t & u of intersect point
        line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_verts - start
        t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
        u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

        # Note: we're trying to check t and u values in bound [0, 1].
        # Since the cost of missing a intersect point (false negative) is too severe,
        # the tolerance has to eagerly catch an intersect [0-TOL, 1+TOL]
        TOL = 1e-9
        parallel = np.abs(line_cross_edge) <= TOL
        intersect_mask = (
            (~parallel) & (t >= -TOL) & (t <= 1 + TOL) & (u >= -TOL) & (u <= 1 + TOL)
        )

        # Calculate intersection points using P = start + t * line_vector
        # Only slice [:2] to grab x and y, ignore z=0
        t_valid = t[intersect_mask]
        intersection_points = start[:2] + t_valid[:, None] * line_vector[:2]
        return intersection_points
