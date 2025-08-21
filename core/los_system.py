from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersect_system import IntersectSystem
import numpy as np
from numpy.typing import NDArray

from core.utils.linear_transform import LinearTransform

_cached_edges: dict[int, tuple[NDArray[np.float64], NDArray[np.float64]]] = {}

# Technically, the entity-to-terrain shouldn't be cached
# Instead, the caller (move action and fire action) should get source's terrain once
# This cache is just to simulate that effect
_cached_source_ent: dict[int, int] = {}


class LosSystem:
    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        return OldLosSystem.check(gs, source_ent, target_ent)


class NewLosSystem:

    @staticmethod
    def _get_poly(
        gs: GameState, source_ent: int
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:

        if source_ent not in _cached_source_ent:
            _cached_source_ent[source_ent] = -1
            for id, terrain, _ in gs.query(TerrainFeature, Transform):
                if terrain.flag & TerrainFeature.Flag.OPAQUE:
                    if IntersectSystem.is_inside(gs, id, source_ent):
                        _cached_source_ent[source_ent] = id

        excluded_terrain_id = _cached_source_ent[source_ent]

        if excluded_terrain_id not in _cached_edges:
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

            if edge_sources == [] or edge_targets == []:
                return (
                    np.array([[]], dtype=np.float64),
                    np.array([[]], dtype=np.float64),
                )
            edge_source = np.vstack(edge_sources)
            edge_target = np.vstack(edge_targets)
            edge_vectors = edge_target - edge_source

            _cached_edges[excluded_terrain_id] = edge_source, edge_vectors

        return _cached_edges[excluded_terrain_id]

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:

        # Ensure two points are float points for a single line vector
        source_pos = gs.get_component(source_ent, Transform).position
        target_pos = gs.get_component(target_ent, Transform).position
        # Explicitly tell numpy that we're working with 2d vectors with z=0
        source = np.array([source_pos.x, source_pos.y, 0], dtype=np.float64)
        target = np.array([target_pos.x, target_pos.y, 0], dtype=np.float64)
        line_vector = target - source

        # Create a vector of edges
        edge_source, edge_vectors = NewLosSystem._get_poly(gs, source_ent)

        # Compute two parametric values t & u of intersect point
        line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
        q1_p1 = edge_source - source
        t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
        u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

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
