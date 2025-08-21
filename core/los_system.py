from numpy.typing import NDArray
from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersect_system import IntersectSystem
import numpy as np

from core.utils.linear_transform import LinearTransform

# TODO: refactor this such that it only cache homogenous edge pairs, not polys
_cached_polys: dict[int, NDArray[np.float64]] = {}


class LosSystem:

    @staticmethod
    def _get_poly(gs: GameState, source_ent: int) -> NDArray[np.float64]:
        excluded_terrain_id = -1
        for id, terrain, _ in gs.query(TerrainFeature, Transform):
            if terrain.flag & TerrainFeature.Flag.OPAQUE:
                if IntersectSystem.is_inside(gs, id, source_ent):
                    excluded_terrain_id = id

        if excluded_terrain_id not in _cached_polys:
            coords_list: list[list[list[float]]] = []
            for id, terrain, transform in gs.query(TerrainFeature, Transform):
                if terrain.flag & TerrainFeature.Flag.OPAQUE:
                    vertices = LinearTransform.apply(terrain.vertices, transform)
                    coords_list.append([[v.x, v.y] for v in vertices])
            _cached_polys[excluded_terrain_id] = np.array(coords_list, dtype=np.float64)

        return _cached_polys[excluded_terrain_id]

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:

        # Ensure two points are float points for a single line vector
        source_pos = gs.get_component(source_ent, Transform).position
        target_pos = gs.get_component(target_ent, Transform).position
        source = np.array([source_pos.x, source_pos.y], dtype=np.float64)
        target = np.array([target_pos.x, target_pos.y], dtype=np.float64)
        line_vector = target - source

        # Create a vector of edges
        polygons = LosSystem._get_poly(gs, source_ent)
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
