from dataclasses import dataclass
from itertools import pairwise
from typing import Iterable

from numba import njit  # type: ignore
import numpy as np
from numpy.typing import NDArray

from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.utils.vec2 import Vec2
from core.utils.linear_transform import LinearTransform


@dataclass
class _Context:

    # This is a no-exclusion terrain data
    np_verts: NDArray[np.float64]
    np_vectors: NDArray[np.float64]
    vert_ids: list[int]
    np_vert_ids: NDArray[np.int64]


# TODO: this global cache is breaking tests, opt to use game state or action level cache
_cache: dict[int, _Context] = {}


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    terrain: TerrainFeature
    terrain_id: int


class IntersectSystem:
    """ECS system for finding line and terrain feature intersections."""

    @staticmethod
    def is_inside(gs: GameState, terrain_id: int, ent: int) -> bool:
        """Checks whether the entity is inside the closed terrain feature."""
        ent_transform = gs.get_component(ent, Transform)
        terrain = gs.get_component(terrain_id, TerrainFeature)
        terrain_transform = gs.get_component(terrain_id, Transform)
        if not terrain.is_closed_loop:
            return False

        # Cast a line from the ent to the right
        # The end point must be further (outside) of polygon
        vertices = LinearTransform.apply(terrain.vertices, terrain_transform)
        vertices.append(vertices[0])
        max_x = max(vertices, key=lambda v: v.x).x
        start = ent_transform.position
        end = Vec2(max_x + 1, ent_transform.position.y)

        is_inside = False
        for b1, b2 in pairwise(vertices):
            point = IntersectSystem._get_intersect(start, end, b1, b2)
            if point is not None:
                is_inside = not is_inside
        return is_inside

    @staticmethod
    def _get_intersect(a1: Vec2, a2: Vec2, b1: Vec2, b2: Vec2) -> Vec2 | None:
        """Return an (x, y) intersection point between 2 line segments."""
        da = a2 - a1  # Delta first segment a
        db = b2 - b1  # Delta second segment b
        if (denom := da.cross(db)) == 0:
            return None  # Lines are parallel
        diff = b1 - a1
        t = diff.cross(db) / denom  # t and a are parametric values for intersection,
        u = diff.cross(da) / denom  # along the length of the vectors using deltas
        if 0 <= t <= 1 and 0 <= u <= 1:
            return a1 + da * t  # Offset p1 point by ua to get final point
        return None  # Intersection is outside the segments

    @staticmethod
    def get(
        gs: GameState, start: Vec2, end: Vec2, mask: int = -1
    ) -> Iterable[Intersection]:
        """Yields intersections between the line segment and terrain."""

        if mask not in _cache:
            _cache[mask] = IntersectSystem.build_context(gs, mask)
        context = _cache[mask]

        intersects = IntersectSystem.njit_check(
            (start.x, start.y),
            (end.x, end.y),
            context.np_verts,
            context.np_vectors,
            context.np_vert_ids,
        )

        for terrain_id in intersects:
            yield Intersection(
                gs.get_component(terrain_id, TerrainFeature),
                terrain_id,
            )

    @staticmethod
    @njit
    def njit_check(
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
        edge_verts: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
        vert_ids: NDArray[np.int64],
    ) -> NDArray[np.int64]:
        # Explicitly tell numpy that we're working with 2d vectors with z=0
        start = np.array([start_pos[0], start_pos[1], 0], dtype=np.float64)
        end = np.array([end_pos[0], end_pos[1], 0], dtype=np.float64)
        line_vector = end - start

        # Compute two parametric values t & u of intersect point
        line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_verts - start
        t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
        u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

        # parallel = np.isclose(line_cross_edge, 0)
        parallel = np.abs(line_cross_edge) <= 1e-8
        intersect_mask = (~parallel) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        intersect_ids = vert_ids[intersect_mask]
        return intersect_ids

    @staticmethod
    def build_context(gs: GameState, mask: int = -1) -> _Context:
        context = _Context(
            np_verts=np.array([], dtype=np.float64),
            np_vectors=np.array([], dtype=np.float64),
            vert_ids=[],
            np_vert_ids=np.array([], dtype=np.int64),
        )

        np_verts: list[tuple[float, float, float]] = []
        np_verts_shift: list[tuple[float, float, float]] = []
        vert_ids: list[int] = []
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & mask) == 0:
                continue
            vertices = LinearTransform.apply(terrain.vertices, transform)
            # Explicitly tell numpy that we're working with 2d vectors with z=0
            np_vert = [(v.x, v.y, 0) for v in vertices]
            np_verts += np_vert
            np_verts_shift += [np_vert[-1]] + np_vert[:-1]  # rolled list
            vert_ids += [id for _ in vertices]

        context.vert_ids = vert_ids
        context.np_vert_ids = np.array(vert_ids)

        if np_verts == [] or np_verts_shift == []:
            np_verts = [(0, 0, 0)]
            np_verts_shift = [(0, 0, 0)]
        edge_start = np.vstack(np_verts, dtype=np.float64)
        edge_end = np.vstack(np_verts_shift, dtype=np.float64)
        edge_vectors = edge_end - edge_start

        context.np_verts = edge_start
        context.np_vectors = edge_vectors

        return context
