from backend import CombatUnit
from core.components import TerrainFeature
from core.world import World
from core.intersects import Intersects


# TODO: check components for LosControls and UnitCondition
class LosChecker:
    """Utility for checking Line-of-Sight (LOS) for combat units."""

    @staticmethod
    def is_spotted(world: World, target_id: int) -> bool:
        """Returns `True` if entity can be spotted by any other entities"""
        if not world.get_component(target_id, CombatUnit):
            return False

        for source_ent, _ in world.get_entities(CombatUnit):
            if source_ent == target_id:
                continue
            is_seen = LosChecker.can_see(world, source_ent, target_id)
            if is_seen:
                return True
        return False

    @staticmethod
    def can_see(world: World, source_ent: int, target_ent: int) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`"""
        if not (source_unit := world.get_component(source_ent, CombatUnit)):
            return False
        if not (target_unit := world.get_component(target_ent, CombatUnit)):
            return False

        # If any OPAQUE terrain exists in the way, return False
        intersects = Intersects.get(
            world=world,
            start=source_unit.position,
            end=target_unit.position,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        return not any(intersects)
