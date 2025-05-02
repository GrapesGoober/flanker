from core.components import Transform, TerrainFeature
from core.ecs import World
from core.intersects import Intersects


# TODO: check components for LosControls and UnitCondition
class LosChecker:
    """Utility for checking Line-of-Sight (LOS) for combat units."""

    @staticmethod
    def is_spotted(world: World, target_id: int) -> bool:
        """Returns `True` if entity can be spotted by any other entities"""
        if not world.get_component(target_id, Transform):
            return False

        for source_ent, _ in world.get_entities(Transform):
            if source_ent == target_id:
                continue
            is_seen = LosChecker.can_see(world, source_ent, target_id)
            if is_seen:
                return True
        return False

    @staticmethod
    def can_see(world: World, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`"""
        if not (source_transform := world.get_component(source_ent, Transform)):
            return False
        if not (target_transform := world.get_component(target_ent, Transform)):
            return False

        # If any OPAQUE terrain exists in the way, return False
        intersects = Intersects.get(
            world=world,
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        return not any(intersects)
