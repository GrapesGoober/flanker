import esper
from components import Transform
from intersects import Intersects
from terrain_types import TerrainFlag


class LosChecker:

    @staticmethod
    def check_all(target_id: int) -> bool:
        if not esper.has_components(target_id, Transform):
            return False
        for source_id, _ in esper.get_component(Transform):
            if source_id == target_id:
                continue
            is_seen = LosChecker.check(source_id, target_id)
            if is_seen:
                return True
        return False

    @staticmethod
    def check(source_id: int, target_id: int) -> bool:
        if not (source_transform := esper.try_component(source_id, Transform)):
            return False
        if not (target_transform := esper.try_component(target_id, Transform)):
            return False

        # TODO: check components for LosControls and UnitCondition

        intersects = Intersects.get(
            start=source_transform.position,
            end=target_transform.position,
            mask=TerrainFlag.OPAQUE,
        )
        return not any(intersects)
