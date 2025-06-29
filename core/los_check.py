from dataclasses import dataclass
from core.components import TerrainFeature, Transform, CombatUnit
from core.gamestate import GameState
from core.intersects import Intersects


@dataclass
class LosContext:
    spotter_id: int
    target_id: int


class LosChecker:
    """Utility for checking Line-of-Sight (LOS) for combat units."""

    @staticmethod
    def check_any(gs: GameState, target_id: int) -> LosContext | None:
        """Returns `LosContext` if entity can be spotted by any other entities."""
        if not gs.get_component(target_id, Transform):
            return None

        for spotter_id, _, _ in gs.query(CombatUnit, Transform):
            if spotter_id == target_id:
                continue
            is_seen = LosChecker.check(gs, spotter_id, target_id)
            if is_seen:
                return LosContext(spotter_id, target_id)
        return None

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
