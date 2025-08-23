from dataclasses import dataclass
from numba import njit  # type: ignore
from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersect_system import IntersectSystem
import numpy as np
from numpy.typing import NDArray

from core.utils.linear_transform import LinearTransform


@dataclass
class _Cache:

    # This is a no-exclusion terrain data
    np_verts: NDArray[np.float64]
    np_vectors: NDArray[np.float64]
    vert_ids: list[int]
    np_vert_ids: NDArray[np.int64]

    # TODO: move system should be responsible for tracking this is_inside
    # for each entity. Simulate for now using cache
    terrain_filter: dict[int, NDArray[np.bool]]


# TODO: this global cache is breaking tests, opt to use game state or action level cache
_cache_init = False
_cache = _Cache(
    np_verts=np.array([], dtype=np.float64),
    np_vectors=np.array([], dtype=np.float64),
    vert_ids=[],
    np_vert_ids=np.array([], dtype=np.int64),
    terrain_filter={},
)


class LosSystem:
    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        return OldLosSystem.check(gs, source_ent, target_ent)


class NewLosSystem:

    @staticmethod
    def build_poly_cache(gs: GameState) -> None:

        np_verts: list[tuple[float, float, float]] = []
        np_verts_shift: list[tuple[float, float, float]] = []
        vert_ids: list[int] = []
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & TerrainFeature.Flag.OPAQUE) == 0:
                continue
            vertices = LinearTransform.apply(terrain.vertices, transform)
            # Explicitly tell numpy that we're working with 2d vectors with z=0
            np_vert = [(v.x, v.y, 0) for v in vertices]
            np_verts += np_vert
            np_verts_shift += [np_vert[-1]] + np_vert[:-1]  # rolled list
            vert_ids += [id for _ in vertices]

        _cache.vert_ids = vert_ids
        _cache.np_vert_ids = np.array(vert_ids)

        if np_verts == [] or np_verts_shift == []:
            np_verts = [(0, 0, 0)]
            np_verts_shift = [(0, 0, 0)]
        edge_start = np.vstack(np_verts, dtype=np.float64)
        edge_end = np.vstack(np_verts_shift, dtype=np.float64)
        edge_vectors = edge_end - edge_start

        _cache.np_verts = edge_start
        _cache.np_vectors = edge_vectors

    @staticmethod
    def build_filter_cache(gs: GameState, spotter_id: int) -> None:
        if spotter_id not in _cache.terrain_filter:
            filter: list[bool] = []
            _cache_inside: dict[int, bool] = {}
            for terrain_id in _cache.vert_ids:
                if terrain_id not in _cache_inside:
                    if IntersectSystem.is_inside(gs, terrain_id, spotter_id):
                        _cache_inside[terrain_id] = False
                    else:
                        _cache_inside[terrain_id] = True
                filter.append(_cache_inside[terrain_id])
            _cache.terrain_filter[spotter_id] = np.array(filter, dtype=np.bool)

    @staticmethod
    def check(gs: GameState, spotter_id: int, target_id: int) -> bool:

        source = gs.get_component(spotter_id, Transform).position
        target = gs.get_component(target_id, Transform).position
        global _cache_init
        if _cache_init == False:
            NewLosSystem.build_poly_cache(gs)
            _cache_init = True
        NewLosSystem.build_filter_cache(gs, spotter_id)

        filter = _cache.terrain_filter[spotter_id]
        return NewLosSystem.njit_check(
            (source.x, source.y),
            (target.x, target.y),
            _cache.np_verts,
            _cache.np_vectors,
            filter,
            _cache.np_vert_ids,
        )

    @staticmethod
    @njit
    def njit_check(
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
        edge_verts: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
        vert_filter: NDArray[np.bool],
        np_vert_ids: NDArray[np.int64],
    ) -> bool:
        # Explicitly tell numpy that we're working with 2d vectors with z=0
        start = np.array([start_pos[0], start_pos[1], 0], dtype=np.float64)
        end = np.array([end_pos[0], end_pos[1], 0], dtype=np.float64)
        line_vector = end - start

        # Filter out terrains
        edge_source = edge_verts[vert_filter]
        edge_vectors = edge_vectors[vert_filter]

        # Compute two parametric values t & u of intersect point
        line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_source - start
        t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
        u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

        # parallel = np.isclose(line_cross_edge, 0)
        parallel = np.abs(line_cross_edge) <= 1e-8
        intersect_mask = (~parallel) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        intersect_ids = np_vert_ids[vert_filter][intersect_mask]

        return int(np.count_nonzero(intersect_mask)) <= 1


class OldLosSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        source_transform = gs.get_component(source_ent, Transform)
        target_transform = gs.get_component(target_ent, Transform)

        intersects = IntersectSystem.get(
            gs=gs,
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )

        # Can see into one other terrain polygon
        passed_one_terrain = False
        for intersect in intersects:
            # Doesn't count current terrain
            if IntersectSystem.is_inside(gs, intersect.terrain_id, source_ent):
                continue
            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True
