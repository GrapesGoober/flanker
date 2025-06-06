from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.intersects import Intersects


class LosChecker:
    """Utility for checking Line-of-Sight (LOS) for combat units."""

    @staticmethod
    def check_any(gs: GameState, target_id: int) -> bool:
        """Returns `True` if entity can be spotted by any other entities."""
        if not gs.get_component(target_id, Transform):
            return False

        for source_ent, _ in gs.query(Transform):
            if source_ent == target_id:
                continue
            is_seen = LosChecker.check(gs, source_ent, target_id)
            if is_seen:
                return True
        return False

    @staticmethod
    def check(gs: GameState, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        if not (source_transform := gs.get_component(source_ent, Transform)):
            return False
        if not (target_transform := gs.get_component(target_ent, Transform)):
            return False

        # If any OPAQUE terrain exists in the way, return False
        intersects = Intersects.get(
            gs=gs,
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        return not any(intersects)
