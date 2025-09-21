from core.components import CombatUnit, TerrainFeature, Transform
from core.gamestate import GameState
from core.systems.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def check(gs: GameState, spotter_ent: int, target_pos: Vec2) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        spotter_transform = gs.get_component(spotter_ent, Transform)
        spotter_unit = gs.get_component(spotter_ent, CombatUnit)

        intersects = IntersectSystem.get(
            gs=gs,
            start=spotter_transform.position,
            end=target_pos,
            mask=TerrainFeature.Flag.OPAQUE,
        )

        # Can see into one other terrain polygon
        passed_one_terrain = False
        spotter_terrain = spotter_unit.inside_terrains or []
        for intersect in intersects:
            # Doesn't count spotter's terrain
            if intersect.terrain_id in spotter_terrain:
                continue
            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True
