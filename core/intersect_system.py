from dataclasses import dataclass
from typing import Iterable

from numba import njit  # type: ignore
import numpy as np
from numpy.typing import NDArray

from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.utils.vec2 import Vec2
from core.utils.linear_transform import LinearTransform


@dataclass
class _TerrainData:
    """Compiled terrain vertices data as numpy arrays and ids"""

    np_verts: NDArray[np.float64]
    np_vectors: NDArray[np.float64]
    vert_ids: list[int]
    np_vert_ids: NDArray[np.int64]


@dataclass
class _Context:
    """Private singleton component for intersect getter."""

    compiled_terrains_by_mask: dict[int, _TerrainData]


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    terrain: TerrainFeature
    terrain_id: int


class IntersectSystem:
    """ECS system for finding line and terrain feature intersections."""

    @staticmethod
    def get(
        gs: GameState, start: Vec2, end: Vec2, mask: int = -1
    ) -> Iterable[Intersection]:
        """Yields intersections between the line segment and terrain."""

        if results := gs.query(_Context):
            _, context = results[0]
        else:
            gs.add_entity(context := _Context({}))
        terrain_datas = context.compiled_terrains_by_mask

        if mask not in terrain_datas:
            terrain_datas[mask] = IntersectSystem._compile_terrain(gs, mask)
        terrain_data = terrain_datas[mask]

        intersects = IntersectSystem._njit_get_intersect(
            (start.x, start.y),
            (end.x, end.y),
            terrain_data.np_verts,
            terrain_data.np_vectors,
            terrain_data.np_vert_ids,
        )

        for terrain_id in intersects:
            yield Intersection(
                gs.get_component(terrain_id, TerrainFeature),
                terrain_id,
            )

    @staticmethod
    @njit
    def _njit_get_intersect(
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
        edge_verts: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
        vert_ids: NDArray[np.int64],
    ) -> NDArray[np.int64]:
        """Returns NDArray of intersected terrain ids."""
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
    def _compile_terrain(gs: GameState, mask: int = -1) -> _TerrainData:
        """Compile all terrain with specified masks into numpy arrays."""
        np_verts_list: list[tuple[float, float, float]] = []
        vert_ids: list[int] = []

        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask == 0:
                continue

            vertices = LinearTransform.apply(terrain.vertices, transform)
            np_vert = [(v.x, v.y, 0) for v in vertices]
            np_verts_list.extend(np_vert)
            vert_ids.extend([id] * len(vertices))

        if not np_verts_list:  # fallback if no terrain matched
            np_verts_list = [(0, 0, 0)]

        edge_start = np.array(np_verts_list, dtype=np.float64)
        edge_end = np.roll(edge_start, shift=-1, axis=0)
        edge_vectors = edge_end - edge_start

        return _TerrainData(
            np_verts=edge_start,
            np_vectors=edge_vectors,
            vert_ids=vert_ids,
            np_vert_ids=np.array(vert_ids, dtype=np.int64),
        )
