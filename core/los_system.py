from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersect_system import IntersectSystem
from core.utils.linear_transform import LinearTransform
from core.utils.vec2 import Vec2


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def _is_inside(gs: GameState, terrain_id: int, ent: int) -> bool:
        """Checks whether the entity is inside the closed terrain feature."""
        ent_transform = gs.get_component(ent, Transform)
        terrain = gs.get_component(terrain_id, TerrainFeature)
        terrain_transform = gs.get_component(terrain_id, Transform)

        # Cast a line from the ent to the right
        # The end point must be further (outside) of polygon
        coords = LinearTransform.apply(terrain.vertices, terrain_transform)
        max_x = max(coords, key=lambda v: v.x).x
        end_point = Vec2(max_x + 1, ent_transform.position.y)
        intersects = IntersectSystem.get(
            gs=gs,
            start=ent_transform.position,
            end=end_point,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        count = 0
        for intersect in intersects:
            if intersect.terrain_id == terrain_id:
                count += 1

        # Even or zero count means outside
        if count % 2 == 0:
            return False
        return True

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
            if LosSystem._is_inside(gs, intersect.terrain_id, source_ent):
                continue
            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True
