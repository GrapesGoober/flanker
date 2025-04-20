import esper
from core.components import Transform
from core.intersects import Intersects
from core.terrain_types import TerrainFlag


# TODO: check components for LosControls and UnitCondition
class LosChecker:
    """Utility for checking Line-of-Sight (LOS) for combat units."""

    @staticmethod
    def is_spotted(target_id: int) -> bool:
        """Returns `True` if entity can be spotted by any other entities"""
        if not esper.has_components(target_id, Transform):
            return False
        for source_id, _ in esper.get_component(Transform):
            if source_id == target_id:
                continue
            is_seen = LosChecker.can_see(source_id, target_id)
            if is_seen:
                return True
        return False

    @staticmethod
    def can_see(source_id: int, target_id: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`"""
        if not (source_transform := esper.try_component(source_id, Transform)):
            return False
        if not (target_transform := esper.try_component(target_id, Transform)):
            return False

        # If any OPAQUE terrain exists in the way, return False
        intersects = Intersects.get(
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFlag.OPAQUE,
        )
        return not any(intersects)
