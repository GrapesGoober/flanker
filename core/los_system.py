from core.components import CombatUnit, TerrainFeature, Transform
from core.gamestate import GameState
from core.intersect_system import IntersectSystem


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        source_transform = gs.get_component(source_ent, Transform)
        target_transform = gs.get_component(target_ent, Transform)
        source_unit = gs.get_component(source_ent, CombatUnit)

        intersects = IntersectSystem.get(
            gs=gs,
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )

        # Can see into one other terrain polygon
        passed_one_terrain = False
        current_terrain = source_unit.inside_terrains or []
        for intersect in intersects:
            # Doesn't count current terrain
            if intersect.terrain_id in current_terrain:
                continue
            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True
