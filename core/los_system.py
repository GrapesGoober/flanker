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
    terrain: tuple[NDArray[np.float64], NDArray[np.float64]]
    edge_ids: list[int]
    edge_ids_array: NDArray[np.int64]

    # TODO: move system should be responsible for tracking this is_inside
    # for each entity. Simulate for now using cache
    terrain_filter: dict[int, NDArray[np.bool]]


# TODO: this global cache is breaking tests, opt to use game state or action level cache
_cache_init = False
_cache = _Cache(
    terrain=(np.array([], dtype=np.float64), np.array([], dtype=np.float64)),
    edge_ids=[],
    edge_ids_array=np.array([], dtype=np.int64),
    terrain_filter={},
)


class LosSystem:
    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        return NewLosSystem.check(gs, source_ent, target_ent)


class NewLosSystem:

    @staticmethod
    def build_poly_cache(gs: GameState, source_ent: int) -> None:

        edge_sources: list[NDArray[np.float64]] = []
        edge_targets: list[NDArray[np.float64]] = []
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & TerrainFeature.Flag.OPAQUE:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                # Explicitly tell numpy that we're working with 2d vectors with z=0
                poly = np.array([[v.x, v.y, 0] for v in vertices], dtype=np.float64)
                shifted_poly = np.roll(poly, shift=-1, axis=0)
                edge_sources.append(poly)
                edge_targets.append(shifted_poly)
                _cache.edge_ids += [id for _ in vertices]

        _cache.edge_ids_array = np.array(_cache.edge_ids)

        if edge_sources == [] or edge_targets == []:
            _cache.terrain = (
                np.array([[0, 0, 0]], dtype=np.float64),
                np.array([[0, 0, 0]], dtype=np.float64),
            )
        edge_source = np.vstack(edge_sources)
        edge_target = np.vstack(edge_targets)
        edge_vectors = edge_target - edge_source

        _cache.terrain = edge_source, edge_vectors

    @staticmethod
    def build_filter_cache(gs: GameState, source_ent: int) -> None:

        filter: list[bool] = []
        _cache_inside: dict[int, bool] = {}
        for terrain_id in _cache.edge_ids:
            if terrain_id not in _cache_inside:
                if IntersectSystem.is_inside(gs, terrain_id, source_ent):
                    _cache_inside[terrain_id] = False
                else:
                    _cache_inside[terrain_id] = True
            filter.append(_cache_inside[terrain_id])
        _cache.terrain_filter[source_ent] = np.array(filter, dtype=np.bool)

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:

        source = gs.get_component(source_ent, Transform).position
        target = gs.get_component(target_ent, Transform).position
        if _cache_init == False:
            NewLosSystem.build_poly_cache(gs, source_ent)
            NewLosSystem.build_filter_cache(gs, source_ent)

        edge_source, edge_vectors = _cache.terrain
        filter = _cache.terrain_filter[source_ent]
        return NewLosSystem._check(
            (source.x, source.y),
            (target.x, target.y),
            edge_source,
            edge_vectors,
            filter,
            _cache.edge_ids_array,
        )

    @staticmethod
    def _check(
        source_pos: tuple[float, float],
        target_pos: tuple[float, float],
        edge_source: NDArray[np.float64],
        edge_vectors: NDArray[np.float64],
        filter: NDArray[np.bool],
        edge_ids_array: NDArray[np.int64],
    ) -> bool:
        # Explicitly tell numpy that we're working with 2d vectors with z=0
        source = np.array([source_pos[0], source_pos[1], 0], dtype=np.float64)
        target = np.array([target_pos[0], target_pos[1], 0], dtype=np.float64)
        line_vector = target - source

        # Filter out terrains
        edge_source = edge_source[filter]
        edge_vectors = edge_vectors[filter]

        # Compute two parametric values t & u of intersect point
        line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_source - source
        t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
        u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

        # parallel = np.isclose(line_cross_edge, 0)
        parallel = np.abs(line_cross_edge) <= 1e-8
        intersect_mask = (~parallel) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        intersect_ids = edge_ids_array[filter][intersect_mask]

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
