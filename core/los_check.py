from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersects import IntersectSystem


class LosCheckSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        if not (source_transform := gs.get_component(source_ent, Transform)):
            return False
        if not (target_transform := gs.get_component(target_ent, Transform)):
            return False

        # If any OPAQUE terrain exists in the way, return False
        intersects = IntersectSystem.get(
            gs=gs,
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        return not any(intersects)
